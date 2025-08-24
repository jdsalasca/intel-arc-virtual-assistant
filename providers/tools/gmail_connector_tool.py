"""
Gmail Connector Tool Provider
Secure Gmail integration with OAuth2 authentication and comprehensive email operations.
"""

import os
import logging
import asyncio
import json
import base64
import pickle
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from core.interfaces.tool_provider import (
    IEmailTool, ToolResult, ToolParameter, ToolCategory, ToolAuthType
)

logger = logging.getLogger(__name__)

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Gmail dependencies not available: {e}")
    GMAIL_AVAILABLE = False
    Request = None
    Credentials = None
    InstalledAppFlow = None
    build = None
    HttpError = None

class GmailConnectorTool(IEmailTool):
    """Gmail integration with secure OAuth2 authentication."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.is_authenticated = False
        
        # OAuth2 configuration
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.compose',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
        
        # Paths for credentials
        self.credentials_dir = Path("credentials")
        self.token_file = self.credentials_dir / "gmail_token.pickle"
        self.credentials_file = self.credentials_dir / "gmail_credentials.json"
        
        # Performance stats
        self.stats = {
            "emails_sent": 0,
            "emails_read": 0,
            "searches_performed": 0,
            "last_sync": None,
            "total_api_calls": 0
        }
        
        # Cache for recent emails
        self.email_cache = {}
        self.cache_duration = timedelta(minutes=15)
    
    def get_tool_name(self) -> str:
        """Get the name of the tool."""
        return "gmail_connector"
    
    def get_tool_description(self) -> str:
        """Get a description of what the tool does."""
        return "Secure Gmail integration for reading, sending, and managing emails"
    
    def get_tool_category(self) -> ToolCategory:
        """Get the category of the tool."""
        return ToolCategory.COMMUNICATION
    
    def get_parameters(self) -> List[ToolParameter]:
        """Get the parameters required by this tool."""
        return [
            ToolParameter(
                name="action",
                type="string",
                description="Action to perform",
                required=True,
                options=["send", "read_recent", "search", "get_unread", "mark_read", "get_labels"]
            ),
            ToolParameter(
                name="to",
                type="string",
                description="Recipient email address (for send action)",
                required=False
            ),
            ToolParameter(
                name="subject",
                type="string", 
                description="Email subject (for send action)",
                required=False
            ),
            ToolParameter(
                name="body",
                type="string",
                description="Email body text (for send action)", 
                required=False
            ),
            ToolParameter(
                name="query",
                type="string",
                description="Search query (for search action)",
                required=False
            ),
            ToolParameter(
                name="count",
                type="number",
                description="Number of emails to retrieve",
                default=10
            ),
            ToolParameter(
                name="include_body",
                type="boolean",
                description="Include email body content",
                default=False
            )
        ]
    
    def get_auth_type(self) -> ToolAuthType:
        """Get the authentication type required."""
        return ToolAuthType.OAUTH
    
    def is_available(self) -> bool:
        """Check if the tool is available and configured."""
        if not GMAIL_AVAILABLE:
            return False
        
        # Check if credentials file exists
        return self.credentials_file.exists() or self.is_authenticated
    
    def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute the Gmail tool."""
        return asyncio.run(self._execute_async(parameters))
    
    async def _execute_async(self, parameters: Dict[str, Any]) -> ToolResult:
        """Async execution for better performance."""
        try:
            # Ensure authentication
            if not self.is_authenticated:
                auth_result = await self._authenticate()
                if not auth_result:
                    return ToolResult(
                        success=False,
                        error="Gmail authentication failed. Please configure OAuth2 credentials."
                    )
            
            # Validate parameters
            if not self.validate_parameters(parameters):
                return ToolResult(
                    success=False,
                    error="Invalid parameters"
                )
            
            action = parameters["action"]
            
            # Route to appropriate method
            if action == "send":
                return await self._send_email(parameters)
            elif action == "read_recent":
                return await self._get_recent_emails(parameters)
            elif action == "search":
                return await self._search_emails(parameters)
            elif action == "get_unread":
                return await self._get_unread_emails(parameters)
            elif action == "mark_read":
                return await self._mark_emails_read(parameters)
            elif action == "get_labels":
                return await self._get_labels()
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
            
        except Exception as e:
            logger.error(f"Gmail tool execution failed: {e}")
            return ToolResult(
                success=False,
                error=f"Gmail operation failed: {str(e)}"
            )
    
    async def _authenticate(self) -> bool:
        """Authenticate with Gmail using OAuth2."""
        if not GMAIL_AVAILABLE:
            logger.error("Gmail dependencies not available")
            return False
        
        try:
            creds = None
            
            # Load existing token
            if self.token_file.exists():
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not self.credentials_file.exists():
                        logger.error(f"Gmail credentials file not found: {self.credentials_file}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file), 
                        self.scopes
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                self.credentials_dir.mkdir(exist_ok=True)
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            # Build service
            self.service = build('gmail', 'v1', credentials=creds)
            self.credentials = creds
            self.is_authenticated = True
            
            logger.info("Gmail authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            return False
    
    async def _send_email(self, parameters: Dict[str, Any]) -> ToolResult:
        """Send an email."""
        try:
            to = parameters.get("to")
            subject = parameters.get("subject", "")
            body = parameters.get("body", "")
            cc = parameters.get("cc")
            bcc = parameters.get("bcc")
            attachments = parameters.get("attachments", [])
            
            if not to:
                return ToolResult(success=False, error="Recipient email address required")
            
            # Create message
            message = self._create_email_message(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
                attachments=attachments
            )
            
            # Send message
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': message}
            ).execute()
            
            self.stats["emails_sent"] += 1
            self.stats["total_api_calls"] += 1
            
            return ToolResult(
                success=True,
                data={
                    "message_id": result["id"],
                    "thread_id": result.get("threadId"),
                    "to": to,
                    "subject": subject,
                    "status": "sent"
                },
                metadata={"action": "send", "api_calls": 1}
            )
            
        except HttpError as e:
            logger.error(f"Gmail API error sending email: {e}")
            return ToolResult(success=False, error=f"Failed to send email: {e}")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return ToolResult(success=False, error=f"Failed to send email: {str(e)}")
    
    def _create_email_message(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        attachments: Optional[List[str]] = None
    ) -> str:
        """Create email message in RFC 2822 format."""
        # Create message container
        if attachments:
            message = MIMEMultipart()
        else:
            message = MIMEText(body, 'plain', 'utf-8')
            message['to'] = to if isinstance(to, str) else ', '.join(to)
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc if isinstance(cc, str) else ', '.join(cc)
            if bcc:
                message['bcc'] = bcc if isinstance(bcc, str) else ', '.join(bcc)
            
            return base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Handle multipart message with attachments
        message['to'] = to if isinstance(to, str) else ', '.join(to)
        message['subject'] = subject
        
        if cc:
            message['cc'] = cc if isinstance(cc, str) else ', '.join(cc)
        if bcc:
            message['bcc'] = bcc if isinstance(bcc, str) else ', '.join(bcc)
        
        # Add body
        message.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Add attachments
        for attachment_path in attachments or []:
            if os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )
                message.attach(part)
        
        return base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    async def _get_recent_emails(self, parameters: Dict[str, Any]) -> ToolResult:
        """Get recent emails."""
        try:
            count = min(parameters.get("count", 10), 50)  # Limit to 50
            include_body = parameters.get("include_body", False)
            
            # Check cache first
            cache_key = f"recent_{count}_{include_body}"
            cached_result = self._get_cached_emails(cache_key)
            if cached_result:
                return cached_result
            
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                maxResults=count
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            # Get details for each message
            for msg in messages:
                email_data = self._get_email_details(msg['id'], include_body)
                if email_data:
                    emails.append(email_data)
            
            result = ToolResult(
                success=True,
                data={
                    "emails": emails,
                    "count": len(emails),
                    "total_available": results.get('resultSizeEstimate', len(emails))
                },
                metadata={
                    "action": "read_recent",
                    "include_body": include_body,
                    "api_calls": len(messages) + 1
                }
            )
            
            # Cache result
            self._cache_emails(cache_key, result)
            
            self.stats["emails_read"] += len(emails)
            self.stats["total_api_calls"] += len(messages) + 1
            
            return result
            
        except HttpError as e:
            logger.error(f"Gmail API error getting recent emails: {e}")
            return ToolResult(success=False, error=f"Failed to get recent emails: {e}")
        except Exception as e:
            logger.error(f"Error getting recent emails: {e}")
            return ToolResult(success=False, error=f"Failed to get recent emails: {str(e)}")
    
    async def _search_emails(self, parameters: Dict[str, Any]) -> ToolResult:
        """Search emails."""
        try:
            query = parameters.get("query", "")
            count = min(parameters.get("count", 10), 50)
            include_body = parameters.get("include_body", False)
            
            if not query:
                return ToolResult(success=False, error="Search query required")
            
            # Perform search
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=count
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            # Get details for each message
            for msg in messages:
                email_data = self._get_email_details(msg['id'], include_body)
                if email_data:
                    emails.append(email_data)
            
            result = ToolResult(
                success=True,
                data={
                    "emails": emails,
                    "query": query,
                    "count": len(emails),
                    "total_matches": results.get('resultSizeEstimate', len(emails))
                },
                metadata={
                    "action": "search",
                    "query": query,
                    "api_calls": len(messages) + 1
                }
            )
            
            self.stats["searches_performed"] += 1
            self.stats["total_api_calls"] += len(messages) + 1
            
            return result
            
        except HttpError as e:
            logger.error(f"Gmail API error searching emails: {e}")
            return ToolResult(success=False, error=f"Failed to search emails: {e}")
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return ToolResult(success=False, error=f"Failed to search emails: {str(e)}")
    
    async def _get_unread_emails(self, parameters: Dict[str, Any]) -> ToolResult:
        """Get unread emails."""
        try:
            count = min(parameters.get("count", 10), 50)
            include_body = parameters.get("include_body", False)
            
            # Search for unread emails
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=count
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            # Get details for each message
            for msg in messages:
                email_data = self._get_email_details(msg['id'], include_body)
                if email_data:
                    emails.append(email_data)
            
            result = ToolResult(
                success=True,
                data={
                    "emails": emails,
                    "unread_count": len(emails),
                    "total_unread": results.get('resultSizeEstimate', len(emails))
                },
                metadata={
                    "action": "get_unread",
                    "api_calls": len(messages) + 1
                }
            )
            
            self.stats["emails_read"] += len(emails)
            self.stats["total_api_calls"] += len(messages) + 1
            
            return result
            
        except HttpError as e:
            logger.error(f"Gmail API error getting unread emails: {e}")
            return ToolResult(success=False, error=f"Failed to get unread emails: {e}")
        except Exception as e:
            logger.error(f"Error getting unread emails: {e}")
            return ToolResult(success=False, error=f"Failed to get unread emails: {str(e)}")
    
    async def _get_labels(self) -> ToolResult:
        """Get Gmail labels."""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            label_data = []
            for label in labels:
                label_data.append({
                    "id": label['id'],
                    "name": label['name'],
                    "type": label.get('type', 'user'),
                    "messages_total": label.get('messagesTotal', 0),
                    "messages_unread": label.get('messagesUnread', 0)
                })
            
            self.stats["total_api_calls"] += 1
            
            return ToolResult(
                success=True,
                data={
                    "labels": label_data,
                    "count": len(label_data)
                },
                metadata={"action": "get_labels", "api_calls": 1}
            )
            
        except HttpError as e:
            logger.error(f"Gmail API error getting labels: {e}")
            return ToolResult(success=False, error=f"Failed to get labels: {e}")
        except Exception as e:
            logger.error(f"Error getting labels: {e}")
            return ToolResult(success=False, error=f"Failed to get labels: {str(e)}")
    
    def _get_email_details(self, message_id: str, include_body: bool = False) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific email."""
        try:
            msg = self.service.users().messages().get(
                userId='me', 
                id=message_id,
                format='full' if include_body else 'metadata'
            ).execute()
            
            # Parse headers
            headers = {}
            for header in msg['payload'].get('headers', []):
                headers[header['name'].lower()] = header['value']
            
            # Extract body if requested
            body = ""
            if include_body:
                body = self._extract_message_body(msg['payload'])
            
            # Parse date
            date_str = headers.get('date', '')
            try:
                # Gmail API returns internal date as milliseconds since epoch
                timestamp = int(msg['internalDate']) / 1000
                date_parsed = datetime.fromtimestamp(timestamp)
            except (KeyError, ValueError):
                date_parsed = datetime.now()
            
            return {
                "id": message_id,
                "thread_id": msg.get('threadId'),
                "subject": headers.get('subject', '(no subject)'),
                "sender": headers.get('from', ''),
                "to": headers.get('to', ''),
                "cc": headers.get('cc', ''),
                "date": date_parsed.isoformat(),
                "snippet": msg.get('snippet', ''),
                "body": body if include_body else None,
                "labels": msg.get('labelIds', []),
                "is_unread": 'UNREAD' in msg.get('labelIds', [])
            }
            
        except HttpError as e:
            logger.error(f"Error getting email details for {message_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting email details: {e}")
            return None
    
    def _extract_message_body(self, payload: Dict[str, Any]) -> str:
        """Extract message body from payload."""
        body = ""
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8')
                elif part['mimeType'] == 'text/html' and not body:
                    # Fallback to HTML if no plain text
                    data = part['body'].get('data', '')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            # Single part message
            if payload['mimeType'] in ['text/plain', 'text/html']:
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    def _get_cached_emails(self, cache_key: str) -> Optional[ToolResult]:
        """Get cached emails if still valid."""
        if cache_key in self.email_cache:
            cached_data, timestamp = self.email_cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
            else:
                del self.email_cache[cache_key]
        return None
    
    def _cache_emails(self, cache_key: str, result: ToolResult):
        """Cache email results."""
        self.email_cache[cache_key] = (result, datetime.now())
        
        # Clean old cache entries
        if len(self.email_cache) > 100:
            self._clean_cache()
    
    def _clean_cache(self):
        """Clean expired cache entries."""
        now = datetime.now()
        expired_keys = []
        
        for key, (_, timestamp) in self.email_cache.items():
            if now - timestamp > self.cache_duration:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.email_cache[key]
    
    def send_email(
        self,
        to: Union[str, List[str]], 
        subject: str, 
        body: str,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        attachments: Optional[List[str]] = None
    ) -> ToolResult:
        """Send an email."""
        parameters = {
            "action": "send",
            "to": to,
            "subject": subject,
            "body": body,
            "cc": cc,
            "bcc": bcc,
            "attachments": attachments or []
        }
        return self.execute(parameters)
    
    def get_recent_emails(self, count: int = 10) -> ToolResult:
        """Get recent emails."""
        parameters = {
            "action": "read_recent",
            "count": count,
            "include_body": False
        }
        return self.execute(parameters)
    
    def search_emails(self, query: str, count: int = 10) -> ToolResult:
        """Search emails by query."""
        parameters = {
            "action": "search",
            "query": query,
            "count": count,
            "include_body": False
        }
        return self.execute(parameters)
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters before execution."""
        action = parameters.get("action")
        if not action:
            return False
        
        if action == "send":
            if not parameters.get("to") or not parameters.get("subject"):
                return False
        
        if action == "search":
            if not parameters.get("query"):
                return False
        
        count = parameters.get("count", 10)
        if not isinstance(count, int) or count < 1 or count > 50:
            return False
        
        return True
    
    def setup_oauth_credentials(self, credentials_json_path: str) -> bool:
        """Setup OAuth2 credentials from downloaded JSON file."""
        try:
            source_path = Path(credentials_json_path)
            if not source_path.exists():
                logger.error(f"Credentials file not found: {credentials_json_path}")
                return False
            
            # Create credentials directory
            self.credentials_dir.mkdir(exist_ok=True)
            
            # Copy credentials file
            with open(source_path, 'r') as source:
                with open(self.credentials_file, 'w') as dest:
                    dest.write(source.read())
            
            logger.info(f"Gmail credentials configured: {self.credentials_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup OAuth credentials: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics."""
        return {
            "tool_name": self.get_tool_name(),
            "is_authenticated": self.is_authenticated,
            "credentials_configured": self.credentials_file.exists(),
            "cache_size": len(self.email_cache),
            "performance": self.stats.copy()
        }