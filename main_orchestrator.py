import asyncio
from gmail_agent import GmailAgent
from telegram_agent import TelegramAgent

# Shared state to avoid duplicate notifications
last_notified_ids = set()

def handle_user_reply(message_id: str, reply_text: str):
    # Called by TelegramAgent when user replies
    print(f"[Orchestrator] User replied to {message_id}: {reply_text}")
    gmail_agent.reply_to_email(message_id, reply_text)
    print(f"[Orchestrator] Reply sent to GmailAgent.")

async def notify_telegram_async(email_details):
    # Async wrapper to call TelegramAgent's async notify_user
    await telegram_agent.notify_user(email_details)

def handle_new_emails(email_details):
    print("[DEBUG] handle_new_emails called with:", email_details)
    # Called by GmailAgent when new emails are found
    # Only notify about truly new emails
    new_emails = [e for e in email_details if e.get('message_id') not in last_notified_ids]
    for e in new_emails:
        last_notified_ids.add(e.get('message_id'))
    if new_emails:
        asyncio.create_task(notify_telegram_async(new_emails))

# Instantiate agents with callbacks
gmail_agent = GmailAgent(notify_callback=handle_new_emails)
telegram_agent = TelegramAgent(on_user_reply=handle_user_reply, gmail_agent=gmail_agent)

async def gmail_polling_loop():
    while True:
        print("[Orchestrator] Checking Gmail for new emails...")
        gmail_agent.check_new_emails(count=3)
        await asyncio.sleep(60)  # 1 minute interval

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Start Gmail polling as a background task
    loop.create_task(gmail_polling_loop())
    # Run the Telegram bot (blocking, in main thread)
    telegram_agent.run()

if __name__ == "__main__":
    main() 