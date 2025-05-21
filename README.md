# Agno Email Agent

Agno Email Agent is a professional, production-ready automation system that integrates Gmail and Telegram using the Agno framework and OpenAI. It enables seamless, intelligent email management and real-time notifications via Telegram, making it ideal for power users, teams, and businesses who want to automate and orchestrate their email workflows.

## Features

- **Gmail Integration:** Read, search, reply, and manage emails using natural language and AI.
- **Telegram Bot:** Receive instant notifications for new emails, reply to emails directly from Telegram, and interact with your inbox on the go.
- **Orchestrated Workflows:** Automated polling, notification, and reply handling between Gmail and Telegram.
- **OpenAI-Powered:** Uses GPT-3.5-turbo (or compatible) for intelligent email parsing, summarization, and suggested replies.
- **Secure by Design:** Sensitive files and secrets are excluded from the repository by default.

## Architecture

```
[Gmail] ←→ [Agno Agent (Python)] ←→ [OpenAI LLM]
     │                                 │
     └────────────→ [Telegram Bot] ←───┘
```
- **main_orchestrator.py:** Runs the orchestrator, polling Gmail and handling Telegram bot events.
- **gmail_agent.py:** Handles all Gmail logic (reading, replying, searching, parsing).
- **telegram_agent.py:** Handles Telegram bot logic, user commands, and notifications.
- **.env.example:** Template for required environment variables.

## Setup & Installation

### Prerequisites
- Python 3.8+
- A Gmail account with API access (OAuth credentials)
- A Telegram bot token ([get one from @BotFather](https://t.me/botfather))
- An OpenAI API key

### 1. Clone the Repository
```bash
git clone https://github.com/raselai/Agno-Email-Agent.git
cd Agno-Email-Agent
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```env
OPENAI_API_KEY=your_openai_api_key_here
TELEGRAM_TOKEN=your_telegram_bot_token_here
# Add Gmail OAuth credentials as needed
```

### 4. Run the Orchestrator
```bash
python main_orchestrator.py
```

## Usage
- Start the orchestrator to enable continuous Gmail polling and Telegram notifications.
- Use Telegram commands:
  - `/start` — Start the bot and register your chat
  - `/check` — Manually check for new emails
  - `/help` — Show help
  - Reply to emails directly from Telegram using the provided format
- All email management is handled securely and intelligently by the Agno Agent.

## Environment Variables
- `OPENAI_API_KEY` — Your OpenAI API key
- `TELEGRAM_TOKEN` — Your Telegram bot token
- (Optional) Gmail OAuth credentials as required by your setup

## Security & Best Practices
- **Sensitive files** (`.env`, `token.json`, `chat_id.txt`) are excluded via `.gitignore`.
- **Never commit real secrets** to the repository.
- If a secret is accidentally committed, revoke it immediately and update your `.gitignore`.

## Contributing
Pull requests, issues, and feature suggestions are welcome! Please open an issue to discuss your ideas or submit a PR.

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

**Agno Email Agent** — Automate your inbox. Stay in control. Powered by Agno, OpenAI, and Telegram.
