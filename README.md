# Daily Summary Bot

Automatically generates a daily summary of your:
- 📅 Google Calendar events
- ✅ Google Tasks (uncompleted)
- 💬 Slack unread messages

Sends the summary directly to Slack each morning.

## Features

- **Google Calendar Integration**: Fetches today's events
- **Google Tasks Integration**: Lists incomplete tasks
- **Slack Scanner**: Counts unread messages in channels/DMs
- **Daily Summary**: Generates a formatted summary
- **Scheduled Execution**: Runs automatically via GitHub Actions

## Setup Instructions

### 1. Get Google API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable these APIs:
   - Google Calendar API
   - Google Tasks API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download the credentials as `credentials.json`
6. Run the app locally once to authorize (it will prompt you to log in)

### 2. Get Slack Bot Token

1. Go to [Slack App Directory](https://api.slack.com/apps)
2. Create a new app
3. Under "OAuth & Permissions", add these scopes:
   - `channels:read`
   - `groups:read`
   - `im:read`
   - `mpim:read`
   - `chat:write`
   - `users:read`
4. Copy your **Bot User OAuth Token** (starts with `xoxb-`)

### 3. Store Secrets in GitHub

1. Go to your repository → Settings → Secrets and variables → Actions
2. Add these secrets:
   - `SLACK_BOT_TOKEN`: Your Slack bot token
   - `SLACK_CHANNEL_ID`: Channel ID where you want summaries (e.g., `C0B4XTBM3NV`)
   - `GOOGLE_CREDENTIALS`: Paste the entire contents of `credentials.json` as a JSON string

### 4. First Run (Local)

```bash
pip install -r requirements.txt
python main.py