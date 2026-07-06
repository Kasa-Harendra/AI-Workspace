from typing import Any
from typing_extensions import TypedDict, Dict, List
from googleapiclient.discovery import Resource, build
from google.auth.credentials import Credentials
import base64
import markdownify
import datetime
import time
import json
import logging
from enum import Enum
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model

from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import User, GoogleAccount, Mail
from settings import settings
from services.authentication import get_creds_from_refresh_token

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_graph.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("agent_graph")

class GmailState(TypedDict):
    google_id: str
    refresh_token: str 
    creds: Credentials 
    first_run: bool
    service: Resource
    mails: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]

def decode_gmail_body(encoded_data: str):
    padded_data = encoded_data + "=" * (4 - len(encoded_data) % 4)
    decoded_bytes = base64.urlsafe_b64decode(padded_data)
    actual_text = decoded_bytes.decode('utf-8')
    return markdownify.markdownify(actual_text, bs4_options={"features": "html.parser"}, strip=["a", "img"])

def get_access_token(state: GmailState):
    logger.info(f"Node 'get_access_token': Fetching token for google_id {state['google_id']}")
    db = SessionLocal()
    try:
        user_acc = db.query(GoogleAccount).filter(GoogleAccount.google_id == state["google_id"]).one()
        state["refresh_token"] = user_acc.refresh_token
        creds = get_creds_from_refresh_token(user_acc.refresh_token)
        state["creds"] = creds
    finally:
        db.close()
    return state

def check_first_run(state: GmailState):
    logger.info("Node 'check_first_run': Checking if this is the first run.")
    db = SessionLocal()
    try:
        count = db.query(Mail).filter(Mail.google_id == state["google_id"]).count()
        state["first_run"] = (count == 0)
        logger.info(f"Node 'check_first_run': first_run set to {state['first_run']}")
    finally:
        db.close()
    return state

def get_gmail_service(state: GmailState):
    logger.info("Node 'get_gmail_service': Building Gmail API service.")
    gmail_service = build("gmail", "v1", credentials=state["creds"])
    state["service"] = gmail_service
    return state

def get_mails(state: GmailState):
    logger.info("Node 'get_mails': Fetching emails from Gmail API.")
    service = state["service"]
    if not state["first_run"]:
        diff = datetime.datetime.now() - datetime.timedelta(hours=settings.SUBSEQUENT_RUN_HOURS)
        unix_timestamp = int(time.mktime(diff.timetuple()))
        result = service.users().messages().list(userId='me', q=f"after:{unix_timestamp}").execute()
        mail_ids = result.get("messages", [])
    else:
        result = service.users().messages().list(userId='me', q=f"newer_than:{settings.FIRST_RUN_DAYS}").execute()
        mail_ids = result.get("messages", [])

    state["mails"] = []
    
    # Process up to a reasonable limit so we don't blow through API limits
    for mail in mail_ids[:50]:
        response = service.users().messages().get(userId="me", id=mail["id"]).execute()
        headers = response["payload"]["headers"]
        required_headers = {"To", "Date", "Subject", "From"}

        header_dict = {}
        for header in headers:
            if header["name"] in required_headers:
                header_dict[header["name"]] = header["value"]
        
        body_data = response["payload"].get("body", {}).get("data", '')
        if not body_data:
            # try to get from parts
            parts = response["payload"].get("parts", [])
            for part in parts:
                if part.get("mimeType") == "text/html":
                    body_data = part.get("body", {}).get("data", "")
                    break
            if not body_data and parts:
                body_data = parts[0].get("body", {}).get("data", "")

        message = {
            "id": response["id"],
            "labelIds": response.get("labelIds", []),
            "headers": header_dict,
            "snippet": response.get("snippet", ""),
            "body": decode_gmail_body(body_data) if body_data else ""
        }
        state["mails"].append(message)

    logger.info(f"Node 'get_mails': Successfully fetched {len(state['mails'])} emails.")
    return state

def create_summaries(state: GmailState):
    logger.info("Node 'create_summaries': Generating summaries using LLM.")
    class CategoryEnum(str, Enum):
        PRIORITY = "Highest-priority-work"
        REVENUE = "Revenue-impacting-items"
        WAITING = "Items-waiting-on-others"
        ATTENTION = "Decisions-requiring-attention"
        DEADLINES= "Upcoming-deadlines"
        RISKS = "Risks"
        NEXT_ACTIONS= "Recommended-next-actions"

    class MailSummary(BaseModel):
        category: CategoryEnum = Field(description="Category that best suits the mail")
        summary: str = Field(description="Summary of the body", default='')

    model = init_chat_model(model=settings.MODEL, model_provider=settings.MODEL_PROVIDER)
    model = model.with_structured_output(MailSummary)

    state["outputs"] = []
    
    for message in state["mails"]:
        prompt = (
            "You are an expert email analyzer. Your task is to accurately categorize the given email "
            "and provide a strictly concise summary of exactly the main content. "
            "Do NOT deviate from the context of the email. Keep the summary to approximately 50 words.\n\n"
            f"Email Data:\n{json.dumps(message)}"
        )
        response = model.invoke(prompt)
        if not response:
            continue
        
        if hasattr(response, 'model_dump'):
            response_dict = response.model_dump()
        else:
            response_dict = response if isinstance(response, dict) else {}

        cat = response_dict.get("category", "")
        res = {
            "id": message["id"],
            "labelIds": message.get("labelIds", []),
            "headers": message["headers"],
            "snippet": message.get("snippet", ""),
            "summary": response_dict.get("summary", ""),
            "category": getattr(cat, 'value', str(cat)) if cat else "Uncategorized"
        }
        state["outputs"].append(res)

    logger.info(f"Node 'create_summaries': Summarized {len(state['outputs'])} emails.")
    return state

def save_to_db(state: GmailState):
    logger.info("Node 'save_to_db': Saving summaries to the database.")
    db = SessionLocal()
    try:
        processed_ids = set()
        for output in state["outputs"]:
            if output["id"] in processed_ids:
                continue
            processed_ids.add(output["id"])
            
            existing = db.query(Mail).filter(Mail.google_id == state["google_id"], Mail.mail_id == output["id"]).first()
            if not existing:
                new_mail = Mail(
                    mail_id=output["id"],
                    google_id=state["google_id"],
                    snippet=output["snippet"] or "",
                    subject=output["headers"].get("Subject", "") or "",
                    summary=output["summary"] or "",
                    category=output["category"] or "Uncategorized"
                )
                db.add(new_mail)
        db.commit()
        logger.info("Node 'save_to_db': Database commit successful.")
    finally:
        db.close()
    return state

# Compile graph
graph_builder = StateGraph(GmailState)

graph_builder.add_node("get_access_token", get_access_token)
graph_builder.add_node("check_first_run", check_first_run)
graph_builder.add_node("get_gmail_service", get_gmail_service)
graph_builder.add_node("get_mails", get_mails)
graph_builder.add_node("create_summaries", create_summaries)
graph_builder.add_node("save_to_db", save_to_db)

graph_builder.add_edge(START, "get_access_token")
graph_builder.add_edge("get_access_token", "check_first_run")
graph_builder.add_edge("check_first_run", "get_gmail_service")
graph_builder.add_edge("get_gmail_service", "get_mails")
graph_builder.add_edge("get_mails", "create_summaries")
graph_builder.add_edge("create_summaries", "save_to_db")
graph_builder.add_edge("save_to_db", END)

graph = graph_builder.compile()

def run_agent_workflow(google_id: str):
    logger.info(f"Starting agent workflow for google_id: {google_id}")
    state = GmailState(
        google_id=google_id,
        refresh_token="",
        creds=None,
        first_run=False,
        service=None,
        mails=[],
        outputs=[]
    )
    graph.invoke(state)
    logger.info(f"Completed agent workflow for google_id: {google_id}")
