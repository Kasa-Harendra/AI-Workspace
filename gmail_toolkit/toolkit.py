from typing import List
from pydantic import Field
from langchain_core.tools import BaseTool
try:
    from langchain_community.agent_toolkits.base import BaseToolkit
except ImportError:
    from langchain_core.tools import BaseToolkit # In older versions it might not be in community

from .client import GMailClient
from .tools import (
    GmailSearchTool,
    GmailGetMessageTool,
    GmailGetThreadTool,
    GmailSendMessageTool,
    GmailCreateDraftTool,
    GmailModifyMessageTool,
    GmailTrashMessageTool,
    GmailUntrashMessageTool,
    GmailDeleteMessageTool,
    GmailModifyThreadTool,
    GmailTrashThreadTool,
    GmailUntrashThreadTool,
    GmailDeleteThreadTool,
    GmailListDraftsTool,
    GmailGetDraftTool,
    GmailUpdateDraftTool,
    GmailSendDraftTool,
    GmailDeleteDraftTool,
    GmailListLabelsTool,
    GmailGetLabelTool,
    GmailCreateLabelTool,
    GmailUpdateLabelTool,
    GmailDeleteLabelTool
)

class GmailToolkit(BaseToolkit):
    """Toolkit for interacting with Gmail."""
    clients: dict = Field(default_factory=dict, exclude=True)

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        api_resources = {email: client.service for email, client in self.clients.items()}
        return [
            GmailSearchTool(api_resources=api_resources),
            GmailGetMessageTool(api_resources=api_resources),
            GmailGetThreadTool(api_resources=api_resources),
            GmailSendMessageTool(api_resources=api_resources),
            GmailCreateDraftTool(api_resources=api_resources),
            GmailModifyMessageTool(api_resources=api_resources),
            GmailTrashMessageTool(api_resources=api_resources),
            GmailUntrashMessageTool(api_resources=api_resources),
            GmailDeleteMessageTool(api_resources=api_resources),
            GmailModifyThreadTool(api_resources=api_resources),
            GmailTrashThreadTool(api_resources=api_resources),
            GmailUntrashThreadTool(api_resources=api_resources),
            GmailDeleteThreadTool(api_resources=api_resources),
            GmailListDraftsTool(api_resources=api_resources),
            GmailGetDraftTool(api_resources=api_resources),
            GmailUpdateDraftTool(api_resources=api_resources),
            GmailSendDraftTool(api_resources=api_resources),
            GmailDeleteDraftTool(api_resources=api_resources),
            GmailListLabelsTool(api_resources=api_resources),
            GmailGetLabelTool(api_resources=api_resources),
            GmailCreateLabelTool(api_resources=api_resources),
            GmailUpdateLabelTool(api_resources=api_resources),
            GmailDeleteLabelTool(api_resources=api_resources),
        ]
