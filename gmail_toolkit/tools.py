from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import base64
from email.message import EmailMessage

class GmailBaseTool(BaseTool):
    """Base class for Gmail tools."""
    api_resource: Any = Field(default=None, description="The Gmail API resource. (Legacy)")
    api_resources: Dict[str, Any] = Field(default_factory=dict, description="Map of email address to Gmail API resource.")

    def get_resource(self, account_email: str) -> Any:
        if self.api_resources:
            if account_email not in self.api_resources:
                raise ValueError(f"Account {account_email} not found or not connected.")
            return self.api_resources[account_email]
        return self.api_resource


class SearchGmailSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    query: str = Field(
        ...,
        description=(
            "The Gmail query to search for. Works exactly like the Gmail search box. "
            "Use standard Gmail search operators like 'from:user@example.com', "
            "'subject:hello', 'has:attachment', 'is:unread', 'after:2023/01/01', 'label:work',"
            "'is:unread newer_than:2h'."
        )
    )
    max_results: int = Field(default=10, description="The maximum number of message results to return.")

class GmailSearchTool(GmailBaseTool):
    name: str = "gmail_search"
    description: str = "Search for Gmail messages or threads."
    args_schema: Type[BaseModel] = SearchGmailSchema

    def _run(self, account_email: str, query: str, max_results: int = 10, **kwargs: Any) -> List[Dict]:
        """Run the tool."""
        results = self.get_resource(account_email).users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()
        return results.get("messages", [])

class GetMessageSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    message_id: str = Field(..., description="The unique ID of the Gmail message to retrieve. Note that this is the ID of the message, not the thread ID.")

class GmailGetMessageTool(GmailBaseTool):
    name: str = "gmail_get_message"
    description: str = "Get a Gmail message by its ID."
    args_schema: Type[BaseModel] = GetMessageSchema

    def _run(self, account_email: str, message_id: str, **kwargs: Any) -> Dict:
        """Run the tool."""
        response = self.get_resource(account_email).users().messages().get(
            userId="me", id=message_id
        ).execute()
        def decode_gmail_body(encoded_data: str):
            import base64
            import markdownify
            padded_data = encoded_data + "=" * (4 - len(encoded_data) % 4)
            decoded_bytes = base64.urlsafe_b64decode(padded_data)
            actual_text = decoded_bytes.decode('utf-8')
            return markdownify.markdownify(actual_text, bs4_options={"features": "html.parser"}, strip=["a", "img"])
        headers = response["payload"]["headers"]
        required_headers = {"To", "Date", "Subject", "From"}

        header_dict = {}
        for header in headers:
            if header["name"] in required_headers:
                header_dict[header["name"]] = header["value"]
        message = {
            "id": response["id"],
            "labelIds": response.get("labelIds", []),
            "headers": header_dict,
            "snippet": response.get("snippet", ""),
            "body": decode_gmail_body(response["payload"]["body"].get("data", ''))
        }
        return message

class GetThreadSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    thread_id: str = Field(..., description="The unique ID of the Gmail thread to retrieve.")

class GmailGetThreadTool(GmailBaseTool):
    name: str = "gmail_get_thread"
    description: str = "Get a Gmail thread by its ID."
    args_schema: Type[BaseModel] = GetThreadSchema

    def _run(self, account_email: str, thread_id: str, **kwargs: Any) -> Dict:
        """Run the tool."""
        thread = self.get_resource(account_email).users().threads().get(
            userId="me", id=thread_id
        ).execute()
        return thread

class SendMessageSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    to: List[str] = Field(..., description="The list of recipient email addresses.")
    subject: str = Field(..., description="The subject line of the email message.")
    message: str = Field(..., description="The plain text body content of the email message.")

class GmailSendMessageTool(GmailBaseTool):
    name: str = "gmail_send_message"
    description: str = "Send a Gmail message."
    args_schema: Type[BaseModel] = SendMessageSchema

    def _run(self, account_email: str, to: List[str], subject: str, message: str, **kwargs: Any) -> Dict:
        """Run the tool."""
        email = EmailMessage()
        email.set_content(message)
        email["To"] = ", ".join(to)
        email["Subject"] = subject
        
        encoded_message = base64.urlsafe_b64encode(email.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        
        sent_message = self.get_resource(account_email).users().messages().send(
            userId="me", body=create_message
        ).execute()
        return sent_message

class CreateDraftSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    to: List[str] = Field(..., description="The list of recipient email addresses for the draft.")
    subject: str = Field(..., description="The subject line of the draft.")
    message: str = Field(..., description="The plain text body content of the draft.")

class GmailCreateDraftTool(GmailBaseTool):
    name: str = "gmail_create_draft"
    description: str = "Create a Gmail draft."
    args_schema: Type[BaseModel] = CreateDraftSchema

    def _run(self, account_email: str, to: List[str], subject: str, message: str, **kwargs: Any) -> Dict:
        """Run the tool."""
        email = EmailMessage()
        email.set_content(message)
        email["To"] = ", ".join(to)
        email["Subject"] = subject
        
        encoded_message = base64.urlsafe_b64encode(email.as_bytes()).decode()
        create_message = {"message": {"raw": encoded_message}}
        
        draft = self.get_resource(account_email).users().drafts().create(
            userId="me", body=create_message
        ).execute()
        return draft


# --- Message Management ---
class ModifyMessageSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    message_id: str = Field(..., description="The ID of the message to modify.")
    add_label_ids: List[str] = Field(default=[], description="A list of IDs of labels to add to this message.")
    remove_label_ids: List[str] = Field(default=[], description="A list of IDs of labels to remove from this message.")

class GmailModifyMessageTool(GmailBaseTool):
    name: str = "gmail_modify_message"
    description: str = "Modify the labels on a Gmail message."
    args_schema: Type[BaseModel] = ModifyMessageSchema

    def _run(self, account_email: str, message_id: str, add_label_ids: List[str] = [], remove_label_ids: List[str] = [], **kwargs: Any) -> Dict:
        body = {"addLabelIds": add_label_ids, "removeLabelIds": remove_label_ids}
        return self.get_resource(account_email).users().messages().modify(userId="me", id=message_id, body=body).execute()

class TrashMessageSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    message_id: str = Field(..., description="The ID of the message to trash.")

class GmailTrashMessageTool(GmailBaseTool):
    name: str = "gmail_trash_message"
    description: str = "Move a Gmail message to the trash."
    args_schema: Type[BaseModel] = TrashMessageSchema

    def _run(self, account_email: str, message_id: str, **kwargs: Any) -> Dict:
        return self.get_resource(account_email).users().messages().trash(userId="me", id=message_id).execute()

class UntrashMessageSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    message_id: str = Field(..., description="The ID of the message to untrash.")

class GmailUntrashMessageTool(GmailBaseTool):
    name: str = "gmail_untrash_message"
    description: str = "Remove a Gmail message from the trash."
    args_schema: Type[BaseModel] = UntrashMessageSchema

    def _run(self, account_email: str, message_id: str, **kwargs: Any) -> Dict:
        return self.get_resource(account_email).users().messages().untrash(userId="me", id=message_id).execute()

class DeleteMessageSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    message_id: str = Field(..., description="The ID of the message to permanently delete.")

class GmailDeleteMessageTool(GmailBaseTool):
    name: str = "gmail_delete_message"
    description: str = "Permanently delete a Gmail message. Use with caution."
    args_schema: Type[BaseModel] = DeleteMessageSchema

    def _run(self, account_email: str, message_id: str, **kwargs: Any) -> str:
        self.get_resource(account_email).users().messages().delete(userId="me", id=message_id).execute()
        return f"Message {message_id} permanently deleted."

# --- Thread Management ---
class ModifyThreadSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    thread_id: str = Field(..., description="The ID of the thread to modify.")
    add_label_ids: List[str] = Field(default=[], description="A list of IDs of labels to add to this thread.")
    remove_label_ids: List[str] = Field(default=[], description="A list of IDs of labels to remove from this thread.")

class GmailModifyThreadTool(GmailBaseTool):
    name: str = "gmail_modify_thread"
    description: str = "Modify the labels on a Gmail thread."
    args_schema: Type[BaseModel] = ModifyThreadSchema

    def _run(self, account_email: str, thread_id: str, add_label_ids: List[str] = [], remove_label_ids: List[str] = [], **kwargs: Any) -> Dict:
        body = {"addLabelIds": add_label_ids, "removeLabelIds": remove_label_ids}
        return self.get_resource(account_email).users().threads().modify(userId="me", id=thread_id, body=body).execute()

class TrashThreadSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    thread_id: str = Field(..., description="The ID of the thread to trash.")

class GmailTrashThreadTool(GmailBaseTool):
    name: str = "gmail_trash_thread"
    description: str = "Move a Gmail thread to the trash."
    args_schema: Type[BaseModel] = TrashThreadSchema

    def _run(self, account_email: str, thread_id: str, **kwargs: Any) -> Dict:
        return self.get_resource(account_email).users().threads().trash(userId="me", id=thread_id).execute()

class UntrashThreadSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    thread_id: str = Field(..., description="The ID of the thread to untrash.")

class GmailUntrashThreadTool(GmailBaseTool):
    name: str = "gmail_untrash_thread"
    description: str = "Remove a Gmail thread from the trash."
    args_schema: Type[BaseModel] = UntrashThreadSchema

    def _run(self, account_email: str, thread_id: str, **kwargs: Any) -> Dict:
        return self.get_resource(account_email).users().threads().untrash(userId="me", id=thread_id).execute()

class DeleteThreadSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    thread_id: str = Field(..., description="The ID of the thread to permanently delete.")

class GmailDeleteThreadTool(GmailBaseTool):
    name: str = "gmail_delete_thread"
    description: str = "Permanently delete a Gmail thread. Use with caution."
    args_schema: Type[BaseModel] = DeleteThreadSchema

    def _run(self, account_email: str, thread_id: str, **kwargs: Any) -> str:
        self.get_resource(account_email).users().threads().delete(userId="me", id=thread_id).execute()
        return f"Thread {thread_id} permanently deleted."

# --- Draft Management ---
class ListDraftsSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    max_results: int = Field(default=10, description="The maximum number of drafts to return.")

class GmailListDraftsTool(GmailBaseTool):
    name: str = "gmail_list_drafts"
    description: str = "List Gmail drafts."
    args_schema: Type[BaseModel] = ListDraftsSchema

    def _run(self, account_email: str, max_results: int = 10, **kwargs: Any) -> List[Dict]:
        results = self.get_resource(account_email).users().drafts().list(userId="me", maxResults=max_results).execute()
        return results.get("drafts", [])

class GetDraftSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    draft_id: str = Field(..., description="The ID of the draft to retrieve.")

class GmailGetDraftTool(GmailBaseTool):
    name: str = "gmail_get_draft"
    description: str = "Get a Gmail draft by its ID."
    args_schema: Type[BaseModel] = GetDraftSchema

    def _run(self, account_email: str, draft_id: str, **kwargs: Any) -> Dict:
        return self.get_resource(account_email).users().drafts().get(userId="me", id=draft_id).execute()

class UpdateDraftSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    draft_id: str = Field(..., description="The ID of the draft to update.")
    to: List[str] = Field(..., description="The list of recipient email addresses.")
    subject: str = Field(..., description="The subject line of the draft.")
    message: str = Field(..., description="The plain text body content of the draft.")

class GmailUpdateDraftTool(GmailBaseTool):
    name: str = "gmail_update_draft"
    description: str = "Update an existing Gmail draft."
    args_schema: Type[BaseModel] = UpdateDraftSchema

    def _run(self, account_email: str, draft_id: str, to: List[str], subject: str, message: str, **kwargs: Any) -> Dict:
        email = EmailMessage()
        email.set_content(message)
        email["To"] = ", ".join(to)
        email["Subject"] = subject
        encoded_message = base64.urlsafe_b64encode(email.as_bytes()).decode()
        
        draft = {"message": {"raw": encoded_message}}
        return self.get_resource(account_email).users().drafts().update(userId="me", id=draft_id, body=draft).execute()

class SendDraftSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    draft_id: str = Field(..., description="The ID of the draft to send.")

class GmailSendDraftTool(GmailBaseTool):
    name: str = "gmail_send_draft"
    description: str = "Send an existing Gmail draft."
    args_schema: Type[BaseModel] = SendDraftSchema

    def _run(self, account_email: str, draft_id: str, **kwargs: Any) -> Dict:
        body = {"id": draft_id}
        return self.get_resource(account_email).users().drafts().send(userId="me", body=body).execute()

class DeleteDraftSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    draft_id: str = Field(..., description="The ID of the draft to delete.")

class GmailDeleteDraftTool(GmailBaseTool):
    name: str = "gmail_delete_draft"
    description: str = "Delete a Gmail draft."
    args_schema: Type[BaseModel] = DeleteDraftSchema

    def _run(self, account_email: str, draft_id: str, **kwargs: Any) -> str:
        self.get_resource(account_email).users().drafts().delete(userId="me", id=draft_id).execute()
        return f"Draft {draft_id} deleted."

# --- Label Management ---
class ListLabelsSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    pass

class GmailListLabelsTool(GmailBaseTool):
    name: str = "gmail_list_labels"
    description: str = "List all Gmail labels."
    args_schema: Type[BaseModel] = ListLabelsSchema

    def _run(self, account_email: str, **kwargs: Any) -> List[Dict]:
        results = self.get_resource(account_email).users().labels().list(userId="me").execute()
        return results.get("labels", [])

class GetLabelSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    label_id: str = Field(..., description="The ID of the label to retrieve.")

class GmailGetLabelTool(GmailBaseTool):
    name: str = "gmail_get_label"
    description: str = "Get a Gmail label by its ID."
    args_schema: Type[BaseModel] = GetLabelSchema

    def _run(self, account_email: str, label_id: str, **kwargs: Any) -> Dict:
        return self.get_resource(account_email).users().labels().get(userId="me", id=label_id).execute()

class CreateLabelSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    name: str = Field(..., description="The display name of the label.")
    label_list_visibility: str = Field(default="labelShow", description="The visibility of the label in the label list. 'labelShow' or 'labelHide'.")
    message_list_visibility: str = Field(default="show", description="The visibility of the label in the message list. 'show' or 'hide'.")

class GmailCreateLabelTool(GmailBaseTool):
    name: str = "gmail_create_label"
    description: str = "Create a new Gmail label."
    args_schema: Type[BaseModel] = CreateLabelSchema

    def _run(self, account_email: str, name: str, label_list_visibility: str = "labelShow", message_list_visibility: str = "show", **kwargs: Any) -> Dict:
        label = {
            "name": name,
            "labelListVisibility": label_list_visibility,
            "messageListVisibility": message_list_visibility
        }
        return self.get_resource(account_email).users().labels().create(userId="me", body=label).execute()

class UpdateLabelSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    label_id: str = Field(..., description="The ID of the label to update.")
    name: str = Field(default=None, description="The new display name of the label.")
    label_list_visibility: str = Field(default=None, description="The visibility of the label in the label list. 'labelShow' or 'labelHide'.")
    message_list_visibility: str = Field(default=None, description="The visibility of the label in the message list. 'show' or 'hide'.")

class GmailUpdateLabelTool(GmailBaseTool):
    name: str = "gmail_update_label"
    description: str = "Update an existing Gmail label."
    args_schema: Type[BaseModel] = UpdateLabelSchema

    def _run(self, account_email: str, label_id: str, name: str = None, label_list_visibility: str = None, message_list_visibility: str = None, **kwargs: Any) -> Dict:
        label = {}
        if name: label["name"] = name
        if label_list_visibility: label["labelListVisibility"] = label_list_visibility
        if message_list_visibility: label["messageListVisibility"] = message_list_visibility
        return self.get_resource(account_email).users().labels().patch(userId="me", id=label_id, body=label).execute()

class DeleteLabelSchema(BaseModel):
    account_email: str = Field(..., description="The email address of the account to perform the action in.")
    label_id: str = Field(..., description="The ID of the label to delete.")

class GmailDeleteLabelTool(GmailBaseTool):
    name: str = "gmail_delete_label"
    description: str = "Delete a Gmail label."
    args_schema: Type[BaseModel] = DeleteLabelSchema

    def _run(self, account_email: str, label_id: str, **kwargs: Any) -> str:
        self.get_resource(account_email).users().labels().delete(userId="me", id=label_id).execute()
        return f"Label {label_id} deleted."
