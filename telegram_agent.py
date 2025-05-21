import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
from typing import Callable, Optional, Dict, List

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramAgent:
    CHAT_ID_FILE = 'chat_id.txt'

    def __init__(self, on_user_reply: Optional[Callable[[str, str], None]] = None, gmail_agent=None):
        self.agent = Agent(
            model=OpenAIChat(id="gpt-3.5-turbo"),
            markdown=True
        )
        self.on_user_reply = on_user_reply
        self.application = None
        self.chat_id = self._load_chat_id()  # Load chat_id from file if present
        self.gmail_agent = gmail_agent  # Reference to GmailAgent for immediate check

    def _save_chat_id(self, chat_id):
        try:
            with open(self.CHAT_ID_FILE, 'w') as f:
                f.write(str(chat_id))
        except Exception as e:
            print(f"[ERROR] Failed to save chat_id: {e}")

    def _load_chat_id(self):
        try:
            if os.path.exists(self.CHAT_ID_FILE):
                with open(self.CHAT_ID_FILE, 'r') as f:
                    return int(f.read().strip())
        except Exception as e:
            print(f"[ERROR] Failed to load chat_id: {e}")
        return None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        self.chat_id = update.effective_chat.id
        self._save_chat_id(self.chat_id)
        welcome_message = (
            f"Hi {user.first_name}! I'm your Email Assistant.\n"
            "Send /check or type 'Check my email' to get your latest unread emails."
        )
        await update.message.reply_text(welcome_message)

    async def check_email_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.chat_id = update.effective_chat.id
        self._save_chat_id(self.chat_id)
        await update.message.reply_text("Checking your Gmail inbox for new emails...")
        if self.gmail_agent:
            emails = self.gmail_agent.check_new_emails(count=3)
            if not emails:
                await update.message.reply_text("No new unread emails found.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        help_text = """
Available commands:
/start - Start the conversation
/help - Show this help message
Just send any message and I'll respond!
        """
        await update.message.reply_text(help_text)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            user_message = update.message.text.strip()
            self.chat_id = update.effective_chat.id
            self._save_chat_id(self.chat_id)
            # If the message is a reply to an email notification, expect format: REPLY <message_id> <your reply>
            if user_message.startswith("REPLY "):
                parts = user_message.split(" ", 2)
                if len(parts) == 3 and self.on_user_reply:
                    message_id, reply_text = parts[1], parts[2]
                    self.on_user_reply(message_id, reply_text)
                    await update.message.reply_text(f"Your reply has been sent to the Gmail Agent for message ID {message_id}.")
                    return
            # Custom command: Check my email
            if user_message.lower() == "check my email":
                await update.message.reply_text("Checking your Gmail inbox for new emails...")
                if self.gmail_agent:
                    emails = self.gmail_agent.check_new_emails(count=3)
                    if not emails:
                        await update.message.reply_text("No new unread emails found.")
                return
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="typing"
            )
            # Get response from Agno agent
            response = self.agent.run(user_message)
            await update.message.reply_text(str(response.content))
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "I apologize, but I encountered an error processing your message. Please try again."
            )

    async def notify_user(self, email_details: List[Dict]):
        print("[DEBUG] TelegramAgent.notify_user called with:", email_details)
        try:
            if not self.chat_id:
                logger.warning("No chat_id set. Cannot notify user.")
                return
            if not email_details:
                await self._send_message("No new emails found.")
                return
            for email in email_details:
                # Use the message_id directly from the parsed JSON
                msg_id = email.get('message_id') or email.get('id')
                print(f"[DEBUG] Sending to Telegram: {msg_id}")
                msg = f"\nNew Email Received:\n"
                msg += f"ID: {msg_id}\nFrom: {email.get('from', '')}\nSubject: {email.get('subject', '')}\nDate: {email.get('date', '')}\nBody: {email.get('body', '')}\n"
                msg += f"\nTo reply, send: REPLY {msg_id} <your reply>"
                await self.application.bot.send_message(chat_id=self.chat_id, text=msg)
        except Exception as e:
            print("[ERROR] Exception in notify_user:", e)

    def run(self):
        telegram_token = os.getenv("TELEGRAM_TOKEN")
        if not telegram_token:
            print("❌ Error: TELEGRAM_TOKEN not found in environment variables")
            return
        print("🤖 Starting Telegram Bot...")
        self.application = Application.builder().token(telegram_token).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("check", self.check_email_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        print("🚀 Bot is running... Press Ctrl+C to stop")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() 