from typing import Optional, List, Callable, Dict
import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.gmail import GmailTools
from rich import print
import typer
from typing_extensions import Annotated
from enum import Enum
import re
import json

# Load environment variables from .env file
load_dotenv()

class EmailAction(str, Enum):
    READ = "read"
    REPLY = "reply"
    SEARCH = "search"
    MANAGE = "manage"
    ALL = "all"
    REPLY_TO = "reply-to"

class GmailAgent:
    def __init__(self, notify_callback: Optional[Callable[[List[Dict]], None]] = None):
        self.agent = Agent(
            model=OpenAIChat(id="gpt-3.5-turbo"),
            tools=[GmailTools()],
            show_tool_calls=True,
            markdown=True
        )
        self.gmail_tools = GmailTools()
        self.notify_callback = notify_callback

    def check_new_emails(self, count: int = 5):
        """
        Checks for new emails using a JSON-based LLM prompt and notifies via callback if set.
        Returns a list of email details (dicts).
        """
        prompt = (
            f"Show me my latest {count} unread emails. For each email, output a JSON object with the following fields: id, thread_id, from, subject, date, body. Output a JSON array of these objects and nothing else."
        )
        response = self.agent.run(prompt)
        print("\n[DEBUG] Raw LLM response for unread emails (JSON expected):\n", response.content)
        emails = []
        try:
            raw = response.content.strip()
            # Remove code block markers if present
            if raw.startswith("```"):
                raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
                raw = re.sub(r"```$", "", raw)
            emails = json.loads(raw)
        except Exception as e:
            print(f"[GmailAgent] Error parsing JSON from LLM: {e}")
        print("\n[DEBUG] Parsed emails list (from JSON):\n", emails)
        print("[DEBUG] Calling notify_callback with emails:", emails)
        if self.notify_callback:
            self.notify_callback(emails)
        return emails

    def _get_body_from_payload(self, payload):
        import base64
        if payload.get("body", {}).get("data"):
            try:
                return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
            except Exception:
                return ""
        # If multipart, try to find the text/plain part
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                try:
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                except Exception:
                    continue
        return ""

    def reply_to_email(self, message_id: str, reply_text: str):
        prompt = f"Send a reply to the email with message ID {message_id} with the following text: {reply_text}"
        response = self.agent.run(prompt)
        return response.content

    def _parse_emails(self, content: str) -> List[Dict]:
        emails = []
        current = {"message_id": "", "from": "", "subject": "", "date": "", "body": "", "thread_id": ""}
        body_lines = []
        for line in content.splitlines():
            line = line.strip()
            # Remove leading bullets, dashes, and markdown
            line = re.sub(r"^[-*\d.\s]*", "", line)
            line = re.sub(r"^\*\*|\*\*$", "", line)
            if not line or line in ("---", "—", "----------------------------------------"):
                if current["message_id"] or current["subject"] or current["from"]:
                    current["body"] = "\n".join(body_lines).strip()
                    emails.append(current.copy())
                current = {"message_id": "", "from": "", "subject": "", "date": "", "body": "", "thread_id": ""}
                body_lines = []
                continue
            if line.startswith("ID:") or line.startswith("Message ID:"):
                # Extract only the alphanumeric message ID (no asterisks, no prefix)
                match = re.search(r'([a-fA-F0-9]{10,})', line)
                if match:
                    current["message_id"] = match.group(1)
                else:
                    current["message_id"] = line.split(":", 1)[1].strip()
            elif line.startswith("Thread ID:"):
                current["thread_id"] = line.split(":", 1)[1].strip()
            elif line.startswith("From:"):
                current["from"] = line.split(":", 1)[1].strip()
            elif line.startswith("Subject:"):
                current["subject"] = line.split(":", 1)[1].strip()
            elif line.startswith("Date:"):
                current["date"] = line.split(":", 1)[1].strip()
            elif line.startswith("Body:"):
                body_lines.append(line.split(":", 1)[1].strip())
            else:
                body_lines.append(line)
        if current["message_id"] or current["subject"] or current["from"]:
            current["body"] = "\n".join(body_lines).strip()
            emails.append(current.copy())
        print("[DEBUG] All parsed emails:", emails)
        return emails

def gmail_assistant(
    action: Annotated[
        EmailAction,
        typer.Option(
            help="Action to perform: read, reply, search, manage, all, or reply-to"
        ),
    ] = EmailAction.ALL,
    count: Annotated[
        int,
        typer.Option(
            help="Number of emails to process"
        ),
    ] = 5,
    query: Annotated[
        Optional[str],
        typer.Option(
            help="Search query or email content"
        ),
    ] = None,
    message_id: Annotated[
        Optional[str],
        typer.Option(
            help="Message ID to reply to (use with reply-to action)"
        ),
    ] = None,
    reply_text: Annotated[
        Optional[str],
        typer.Option(
            help="Text to reply with (use with reply-to action)"
        ),
    ] = None,
    labels: Annotated[
        Optional[List[str]],
        typer.Option(
            help="Labels to filter by (comma-separated)"
        ),
    ] = None,
):
    """Gmail Assistant powered by Agno and OpenAI"""
    
    # Initialize the agent with Gmail tools and GPT-3.5-turbo
    agent = Agent(
        model=OpenAIChat(id="gpt-3.5-turbo"),
        tools=[GmailTools()],
        show_tool_calls=True,
        markdown=True
    )

    try:
        if action == EmailAction.READ or action == EmailAction.ALL:
            print("\n📥 Reading latest unread emails...")
            agent.print_response("""Show me my latest {count} unread emails. For each email, display:
1. Message ID (prefix with 'ID: ')
2. From
3. Subject
4. Date
5. Body

Format each email clearly with separators and make the Message ID prominent.""".format(count=count))

        if action == EmailAction.SEARCH and query:
            print(f"\n🔍 Searching emails for: {query}")
            agent.print_response("""Search my emails for '{query}' and show me the top {count} results. For each email, display:
1. Message ID (prefix with 'ID: ')
2. From
3. Subject
4. Date
5. Body

Format each email clearly with separators and make the Message ID prominent.""".format(query=query, count=count))

        if action == EmailAction.REPLY or action == EmailAction.ALL:
            print("\n↩️ Checking emails that need replies...")
            agent.print_response("""Find {count} important emails that need replies. For each email, display:
1. Message ID (prefix with 'ID: ')
2. From
3. Subject
4. Date
5. Body
6. Suggested Reply

Format each email clearly with separators and make the Message ID prominent.""".format(count=count))

        if action == EmailAction.MANAGE or action == EmailAction.ALL:
            print("\n📊 Managing inbox...")
            agent.print_response(f"Analyze my latest {count} emails and suggest organization actions (archive, label, etc.)")
            
        if action == EmailAction.REPLY_TO and message_id:
            if not reply_text:
                print("\n✍️ Getting email details and suggesting a reply...")
                agent.print_response("""Get the email with message ID {message_id}. Show:
1. Message ID (prefix with 'ID: ')
2. From
3. Subject
4. Date
5. Body
6. Suggested Reply

Format the email clearly and make the Message ID prominent.""".format(message_id=message_id))
            else:
                print("\n✉️ Sending reply...")
                agent.print_response(f"Reply to the email with message ID {message_id} with the following text: {reply_text}")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nPlease make sure you have:")
        print("1. Set up your Google OAuth credentials in the .env file")
        print("2. Set your OpenAI API key in the .env file")
        print("3. Completed the Google OAuth authentication process")
        if action == EmailAction.REPLY_TO:
            print("4. Provided a valid message ID (you can get this from the read command)")

if __name__ == "__main__":
    typer.run(gmail_assistant) 