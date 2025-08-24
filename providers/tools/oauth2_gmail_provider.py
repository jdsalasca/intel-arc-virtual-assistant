"""
OAuth2 Gmail Provider with Email Response Capabilities
Enterprise-grade Gmail integration with OAuth2 authentication and AI-powered email responses.
"""

import os
import json
import logging
import asyncio
import base64
import pickle
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.interfaces.tool_provider import IToolProvider, ToolCapability, ToolCategory

logger = logging.getLogger(__name__)

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Gmail OAuth2 dependencies not available: {e}")
    GMAIL_AVAILABLE = False
    Request = None
    Credentials = None
    InstalledAppFlow = None
    build = None
    HttpError = None

class OAuth2GmailProvider(IToolProvider):
    """OAuth2-enabled Gmail provider with AI-powered email responses."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.user_email = None
        
        # OAuth2 configuration
        self.SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.compose',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
        
        # Paths for credentials
        self.credentials_dir = Path("credentials")
        self.credentials_dir.mkdir(exist_ok=True)
        self.client_secrets_file = self.credentials_dir / "gmail_client_secrets.json"
        self.token_file = self.credentials_dir / "gmail_token.pickle"
        
        # Email processing configuration
        self.max_emails_per_request = 50
        self.email_cache = {}
        
        # AI response settings
        self.auto_response_enabled = False
        self.response_templates = {
            "acknowledgment": "Thank you for your email. I've received your message and will get back to you soon.",
            "out_of_office": "I'm currently out of the office and will respond when I return.",
            "meeting_request": "Thank you for the meeting request. I'll check my calendar and get back to you."
        }
    
    def get_tool_name(self) -> str:
        """Get the tool name."""
        return "oauth2_gmail"
    
    def get_description(self) -> str:
        """Get tool description."""
        return "OAuth2-enabled Gmail integration with AI-powered email management and response capabilities"
    
    def get_capabilities(self) -> List[ToolCapability]:
        """Get list of tool capabilities."""
        return [
            ToolCapability.EMAIL_READ,
            ToolCapability.EMAIL_SEND,
            ToolCapability.EMAIL_SEARCH,
            ToolCapability.EMAIL_MANAGE
        ]
    
    def get_category(self) -> ToolCategory:
        """Get tool category."""
        return ToolCategory.COMMUNICATION
    
    def is_available(self) -> bool:
        """Check if Gmail OAuth2 functionality is available."""
        return GMAIL_AVAILABLE and self.client_secrets_file.exists()
    
    async def initialize(self, **kwargs) -> bool:
        """Initialize OAuth2 Gmail provider."""
        if not GMAIL_AVAILABLE:
            logger.error("Gmail OAuth2 dependencies not available")
            return False
        
        try:
            # Load or create credentials
            await self._authenticate()
            
            if self.credentials:
                # Build Gmail service
                self.service = build('gmail', 'v1', credentials=self.credentials)
                
                # Get user profile
                profile = self.service.users().getProfile(userId='me').execute()
                self.user_email = profile.get('emailAddress')
                
                logger.info(f"✅ OAuth2 Gmail initialized for: {self.user_email}")
                return True
            else:
                logger.error("Failed to obtain Gmail credentials")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize OAuth2 Gmail: {e}")
            return False
    
    async def _authenticate(self) -> bool:
        """Handle OAuth2 authentication flow."""
        creds = None
        
        # Load existing token
        if self.token_file.exists():
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                logger.warning(f"Failed to load existing token: {e}")
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Gmail credentials refreshed")
                except Exception as e:
                    logger.warning(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not self.client_secrets_file.exists():
                    logger.error(f"Gmail client secrets file not found: {self.client_secrets_file}")
                    return False
                
                # Start OAuth2 flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.client_secrets_file),
                    self.SCOPES
                )
                
                # Run local server for OAuth callback
                creds = flow.run_local_server(port=0)
                logger.info("New Gmail credentials obtained")
            
            # Save credentials
            try:
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info("Gmail credentials saved")
            except Exception as e:
                logger.warning(f"Failed to save credentials: {e}")
        
        self.credentials = creds
        return creds is not None
    
    async def execute_tool(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Gmail tool action."""
        if not self.service:
            return {"error": "Gmail service not initialized"}
        
        try:
            if action == "read_emails":
                return await self._read_emails(parameters)
            elif action == "send_email":
                return await self._send_email(parameters)
            elif action == "reply_to_email":
                return await self._reply_to_email(parameters)
            elif action == "search_emails":
                return await self._search_emails(parameters)
            elif action == "get_unread_count":
                return await self._get_unread_count()
            elif action == "mark_as_read":
                return await self._mark_as_read(parameters)
            elif action == "generate_ai_response":
                return await self._generate_ai_response(parameters)
            elif action == "auto_respond":
                return await self._auto_respond_to_emails(parameters)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Gmail tool execution failed: {e}")
            return {"error": str(e)}
    
    async def _read_emails(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Read emails with filtering options."""
        query = parameters.get("query", "")
        max_results = min(parameters.get("max_results", 10), self.max_emails_per_request)
        include_body = parameters.get("include_body", True)
        
        try:
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                email_data = await self._get_email_details(message['id'], include_body)
                if email_data:
                    emails.append(email_data)
            
            return {
                "success": True,
                "emails": emails,
                "total_count": len(emails),
                "query": query
            }
            
        except HttpError as e:
            return {"error": f"Gmail API error: {e}"}
    
    async def _get_email_details(self, message_id: str, include_body: bool = True) -> Optional[Dict[str, Any]]:
        """Get detailed email information."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full' if include_body else 'metadata'
            ).execute()
            
            # Extract headers
            headers = {}
            for header in message['payload'].get('headers', []):
                headers[header['name'].lower()] = header['value']
            
            # Extract body
            body = ""
            if include_body:
                body = self._extract_email_body(message['payload'])
            
            # Check if unread
            is_unread = 'UNREAD' in message.get('labelIds', [])
            
            email_data = {
                "id": message_id,
                "thread_id": message.get('threadId'),
                "subject": headers.get('subject', 'No Subject'),
                "from": headers.get('from', 'Unknown'),
                "to": headers.get('to', ''),
                "date": headers.get('date', ''),
                "body": body,
                "is_unread": is_unread,
                "labels": message.get('labelIds', []),
                "snippet": message.get('snippet', '')
            }
            
            return email_data
            
        except Exception as e:
            logger.error(f"Failed to get email details for {message_id}: {e}")
            return None
    
    def _extract_email_body(self, payload: Dict) -> str:
        """Extract email body from payload."""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html' and not body:
                    data = part['body'].get('data', '')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body.strip()
    
    async def _send_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send an email."""
        to = parameters.get("to", "")
        subject = parameters.get("subject", "")
        body = parameters.get("body", "")
        cc = parameters.get("cc", "")
        bcc = parameters.get("bcc", "")
        
        if not to or not subject:
            return {"error": "Missing required fields: to, subject"}
        
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            message['from'] = self.user_email
            
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return {
                "success": True,
                "message_id": sent_message['id'],
                "to": to,
                "subject": subject
            }
            
        except Exception as e:
            return {"error": f"Failed to send email: {e}"}
    
    async def _reply_to_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Reply to an email."""
        message_id = parameters.get("message_id", "")
        reply_body = parameters.get("reply_body", "")
        
        if not message_id or not reply_body:
            return {"error": "Missing required fields: message_id, reply_body"}
        
        try:
            # Get original message
            original = self.service.users().messages().get(
                userId='me',
                id=message_id
            ).execute()
            
            # Extract headers for reply
            headers = {}
            for header in original['payload'].get('headers', []):
                headers[header['name'].lower()] = header['value']
            
            # Create reply
            reply = MIMEText(reply_body)
            reply['to'] = headers.get('from', '')
            reply['subject'] = f"Re: {headers.get('subject', '')}"
            reply['from'] = self.user_email
            reply['in-reply-to'] = headers.get('message-id', '')
            reply['references'] = headers.get('message-id', '')
            
            # Send reply
            raw_reply = base64.urlsafe_b64encode(reply.as_bytes()).decode('utf-8')
            
            sent_reply = self.service.users().messages().send(
                userId='me',
                body={
                    'raw': raw_reply,
                    'threadId': original.get('threadId')
                }
            ).execute()
            
            return {
                "success": True,
                "reply_id": sent_reply['id'],
                "original_id": message_id,
                "thread_id": original.get('threadId')
            }
            
        except Exception as e:
            return {"error": f"Failed to reply to email: {e}"}
    
    async def _search_emails(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search emails with advanced query."""
        query = parameters.get("query", "")
        max_results = min(parameters.get("max_results", 20), self.max_emails_per_request)
        
        if not query:
            return {"error": "Search query is required"}
        
        return await self._read_emails({
            "query": query,
            "max_results": max_results,
            "include_body": False
        })
    
    async def _get_unread_count(self) -> Dict[str, Any]:
        """Get count of unread emails."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=1
            ).execute()
            
            # Get total count from estimated results
            unread_count = results.get('resultSizeEstimate', 0)
            
            return {
                "success": True,
                "unread_count": unread_count
            }
            
        except Exception as e:
            return {"error": f"Failed to get unread count: {e}"}
    
    async def _mark_as_read(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Mark emails as read."""
        message_ids = parameters.get("message_ids", [])
        
        if not message_ids:
            return {"error": "No message IDs provided"}
        
        try:
            # Remove UNREAD label
            self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': message_ids,
                    'removeLabelIds': ['UNREAD']
                }
            ).execute()
            
            return {
                "success": True,
                "marked_count": len(message_ids)
            }
            
        except Exception as e:
            return {"error": f"Failed to mark as read: {e}"}
    
    async def _generate_ai_response(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered email response."""
        email_content = parameters.get("email_content", "")
        response_type = parameters.get("response_type", "professional")
        context = parameters.get("context", "")
        
        if not email_content:
            return {"error": "Email content is required"}
        
        # This would integrate with your AI model
        # For now, using template-based responses
        if response_type in self.response_templates:
            response = self.response_templates[response_type]
        else:
            response = f"Thank you for your email. I'll review your message and respond accordingly."
        
        # Add context if provided
        if context:
            response += f"\n\nContext: {context}"
        
        return {
            "success": True,
            "generated_response": response,
            "response_type": response_type
        }
    
    async def _auto_respond_to_emails(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-respond to unread emails with AI-generated responses."""
        max_responses = parameters.get("max_responses", 5)
        response_type = parameters.get("response_type", "acknowledgment")
        
        if not self.auto_response_enabled:
            return {"error": "Auto-response is not enabled"}
        
        try:
            # Get unread emails
            unread_emails = await self._read_emails({
                "query": "is:unread",
                "max_results": max_responses,
                "include_body": True
            })
            
            if not unread_emails.get("success"):
                return unread_emails
            
            responses_sent = 0
            for email in unread_emails.get("emails", []):
                # Generate response
                ai_response = await self._generate_ai_response({
                    "email_content": email.get("body", ""),
                    "response_type": response_type
                })
                
                if ai_response.get("success"):
                    # Send reply
                    reply_result = await self._reply_to_email({
                        "message_id": email["id"],
                        "reply_body": ai_response["generated_response"]
                    })
                    
                    if reply_result.get("success"):
                        responses_sent += 1
                        
                        # Mark as read
                        await self._mark_as_read({
                            "message_ids": [email["id"]]
                        })
            
            return {
                "success": True,
                "responses_sent": responses_sent,
                "emails_processed": len(unread_emails.get("emails", []))
            }
            
        except Exception as e:
            return {"error": f"Auto-response failed: {e}"}
    
    def get_oauth_authorization_url(self) -> str:
        """Get OAuth2 authorization URL for web interface."""
        if not self.client_secrets_file.exists():
            return ""
        
        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.client_secrets_file),
            self.SCOPES
        )
        
        flow.redirect_uri = 'http://localhost:8000/oauth/gmail/callback'
        auth_url, _ = flow.authorization_url(prompt='consent')
        return auth_url
    
    def set_auto_response(self, enabled: bool, response_type: str = "acknowledgment"):
        """Enable/disable auto-response feature."""
        self.auto_response_enabled = enabled
        if enabled:
            logger.info(f"Auto-response enabled with type: {response_type}")
        else:
            logger.info("Auto-response disabled")
    
    def get_status(self) -> Dict[str, Any]:
        """Get provider status."""
        return {
            "provider": "OAuth2Gmail",
            "authenticated": self.credentials is not None,
            "user_email": self.user_email,
            "auto_response_enabled": self.auto_response_enabled,
            "service_available": self.service is not None
        }