# Ambassador Singularity Bot

Telegram bot for managing the Singularity ambassador program, helping students track their referrals and earn points.

## Features
- Participant registration
- Lead tracking and registration
- Information sharing about Singularity programs
- Points tracking and statistics
- Push notifications

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Telegram bot token:
```
BOT_TOKEN=your_bot_token_here
```

3. Run the bot:
```bash
python bot.py
```

## Commands
- `/start` - Start the bot and see welcome message
- `/about` - View competition rules
- `/user` - Register as a participant
- `/add` - Add a new lead
- `/info` - Get information about Singularity programs
- `/stats` - View your points and ranking 