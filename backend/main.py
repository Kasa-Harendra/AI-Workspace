import jwt
import datetime
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
import os
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt

from settings import settings
from db.database import engine, get_db, SessionLocal
from db import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

def ensure_default_user():
    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            default_user = models.User(
                username="admin",
                hashed_password=bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            )
            db.add(default_user)
            db.commit()
    finally:
        db.close()

ensure_default_user()

app = FastAPI()

# Allow frontend to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:8088", "http://127.0.0.1:8088",
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:8000", "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_jwt_token(user_id: int):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthRequest(BaseModel):
    code: str

@app.post("/api/auth/register")
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == req.username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = models.User(
        username=req.username,
        hashed_password=get_password_hash(req.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_jwt_token(new_user.id)
    return {"status": "success", "token": token, "user": {"id": new_user.id, "username": new_user.username}}

@app.post("/api/auth/login")
def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    token = create_jwt_token(user.id)
    return {"status": "success", "token": token, "user": {"id": user.id, "username": user.username}}

@app.post("/api/auth/google")
def authenticate_with_google(auth_req: AuthRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    client_config = {
        "web": {
            "client_id": settings.CLIENT_ID,
            "project_id": "agentworkspace-501008",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": settings.CLIENT_SECRET,
            "redirect_uris": ["postmessage"]
        }
    }
    
    try:
        flow = Flow.from_client_config(
            client_config,
            scopes=['openid', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/calendar']
        )
        flow.redirect_uri = 'postmessage'
        
        # Swap code for tokens
        flow.fetch_token(code=auth_req.code)
        credentials = flow.credentials
        
        # Verify the ID Token
        user_info = id_token.verify_oauth2_token(
            credentials.id_token, google_requests.Request(), settings.CLIENT_ID
        )
        
        google_id = user_info['sub']
        email = user_info['email']
        name = user_info.get('name', email)
        
        # Check if Google Account exists
        google_account = db.query(models.GoogleAccount).filter(models.GoogleAccount.google_id == google_id).first()
        
        if not google_account:
            google_account = models.GoogleAccount(
                google_id=google_id,
                user_id=current_user.id,
                name=name,
                email=email,
                refresh_token=credentials.refresh_token or ""
            )
            db.add(google_account)
            db.commit()
            db.refresh(google_account)
        elif google_account.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="This Google account is linked to another user")
        elif credentials.refresh_token:
            google_account.refresh_token = credentials.refresh_token
            google_account.name = name
            google_account.email = email
            db.commit()
            db.refresh(google_account)
            
        return {
            "status": "success",
            "message": "Google account linked successfully",
            "account": {
                "google_id": google_account.google_id,
                "name": google_account.name,
                "email": google_account.email
            }
        }
    except Exception as e:
        print(f"Failed to authenticate: {e}")
        raise HTTPException(status_code=400, detail="Authentication failed")

@app.get("/api/accounts")
def get_accounts(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.query(models.GoogleAccount).filter(models.GoogleAccount.user_id == current_user.id).all()
    return {
        "status": "success",
        "accounts": [
            {"google_id": acc.google_id, "name": acc.name, "email": acc.email} for acc in accounts
        ]
    }

@app.delete("/api/accounts/{google_id}")
def delete_account(google_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(models.GoogleAccount).filter(models.GoogleAccount.google_id == google_id, models.GoogleAccount.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Google account not found")
    
    db.delete(account)
    db.commit()
    return {"status": "success", "message": "Google account removed successfully"}

class AgentRunRequest(BaseModel):
    google_id: str

@app.post("/api/agent/run")
def run_agent(req: AgentRunRequest, background_tasks: BackgroundTasks, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(models.GoogleAccount).filter(models.GoogleAccount.google_id == req.google_id, models.GoogleAccount.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Google account not found or not linked to current user")
    
    from services.agent import run_agent_workflow
    background_tasks.add_task(run_agent_workflow, req.google_id)
    return {"status": "success", "message": "Agent execution started in the background"}

@app.post("/api/auth/link-google")
def link_google_account(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        from services.authentication import authenticate_google_workspace
        creds = authenticate_google_workspace()
        from googleapiclient.discovery import build
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        email = profile['emailAddress']
        google_id = profile.get('emailAddress')
        
        account = db.query(models.GoogleAccount).filter(models.GoogleAccount.email == email).first()
        if not account:
            account = models.GoogleAccount(
                google_id=google_id,
                user_id=current_user.id,
                name=email,
                email=email,
                refresh_token=creds.refresh_token or ""
            )
            db.add(account)
        else:
            account.user_id = current_user.id
            if creds.refresh_token:
                account.refresh_token = creds.refresh_token
        db.commit()
        return {"status": "success", "email": email, "google_id": google_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to authenticate with Google: {str(e)}")

@app.get("/api/mails")
def get_user_mails(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.query(models.GoogleAccount).filter(models.GoogleAccount.user_id == current_user.id).all()
    google_ids = [acc.google_id for acc in accounts]
    if not google_ids:
        return {"status": "success", "mails": [], "message": "No Google Mail account linked"}
    
    mails = db.query(models.Mail).filter(models.Mail.google_id.in_(google_ids)).all()
    return {
        "status": "success",
        "mails": [
            {
                "mail_id": mail.mail_id,
                "google_id": mail.google_id,
                "snippet": mail.snippet,
                "subject": mail.subject,
                "summary": mail.summary,
                "category": mail.category
            } for mail in mails
        ]
    }

class ChatRequest(BaseModel):
    query: str

@app.post("/api/copilot-chat")
def copilot_chat(req: ChatRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.query(models.GoogleAccount).filter(models.GoogleAccount.user_id == current_user.id).all()
    google_ids = [acc.google_id for acc in accounts]
    if not google_ids:
        return {"status": "error", "reply": "⚠️ Please click 'Sign in with Google Mail' first to analyze your inbox."}
    
    mails = db.query(models.Mail).filter(models.Mail.google_id.in_(google_ids)).all()
    context_str = "\n".join([f"[{m.category}] Subject: {m.subject} | Summary: {m.summary}" for m in mails[:20]])
    
    from langchain.chat_models import init_chat_model
    model = init_chat_model(model=settings.MODEL, model_provider=settings.MODEL_PROVIDER)
    
    prompt = (
        f"You are the Executive Copilot for an AI Workspace. The user asks: '{req.query}'.\n"
        f"Here are the user's categorized emails from the database:\n{context_str}\n\n"
        "Provide a helpful, executive, concise answer based on their emails."
    )
    try:
        res = model.invoke(prompt)
        reply = getattr(res, "content", str(res))
    except Exception as e:
        reply = f"I am ready to analyze your emails! (LLM Note: {str(e)})"
        
    return {"status": "success", "reply": reply}

@app.get("/")
@app.get("/index.html")
def serve_frontend():
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"status": "error", "message": "Frontend UI not found at frontend/index.html"}


