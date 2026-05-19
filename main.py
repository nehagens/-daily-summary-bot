#!/usr/bin/env python3
"""
Daily Summary Bot
Fetches Google Calendar, Google Tasks, and Slack unread messages
Sends a formatted summary to Slack
"""

import os
import json
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Scopes for Google APIs
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
TASKS_SCOPES = ['https://www.googleapis.com/auth/tasks.readonly']

class DailySummaryBot:
    def __init__(self):
        self.slack_token = os.getenv('SLACK_BOT_TOKEN')
        self.slack_channel = os.getenv('SLACK_CHANNEL_ID')
        self.google_creds_json = os.getenv('GOOGLE_CREDENTIALS')
        
        if not self.slack_token or not self.slack_channel:
            raise ValueError("Missing SLACK_BOT_TOKEN or SLACK_CHANNEL_ID environment variables")
        
        self.slack_client = WebClient(token=self.slack_token)
        self.calendar_service = None
        self.tasks_service = None
        
    def authenticate_google(self):
        """Authenticate with Google APIs"""
        try:
            if self.google_creds_json:
                creds_dict = json.loads(self.google_creds_json)
                creds = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=CALENDAR_SCOPES + TASKS_SCOPES
                )
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json',
                    scopes=CALENDAR_SCOPES + TASKS_SCOPES
                )
                creds = flow.run_local_server(port=0)
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.calendar_service = build('calendar', 'v3', credentials=creds)
            self.tasks_service = build('tasks', 'v1', credentials=creds)
            print("✓ Google authentication successful")
            
        except Exception as e:
            print(f"✗ Google authentication failed: {e}")
            raise

    def get_calendar_events(self):
        """Get today's calendar events"""
        try:
            now = datetime.utcnow()
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
            end_of_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
            
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=start_of_day,
                timeMax=end_of_day,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            print(f"✓ Found {len(events)} calendar events")
            return events
            
        except Exception as e:
            print(f"✗ Calendar fetch failed: {e}")
            return []

    def get_tasks(self):
        """Get incomplete tasks"""
        try:
            tasks_result = self.tasks_service.tasklists().list().execute()
            tasklists = tasks_result.get('items', [])
            
            all_tasks = []
            for tasklist in tasklists:
                tasks = self.tasks_service.tasks().list(
                    tasklist=tasklist['id'],
                    showCompleted=False,
                    showHidden=False
                ).execute()
                all_tasks.extend(tasks.get('items', []))
            
            print(f"✓ Found {len(all_tasks)} incomplete tasks")
            return all_tasks
            
        except Exception as e:
            print(f"✗ Tasks fetch failed: {e}")
            return []

    def get_slack_unread(self):
        """Get unread message count from Slack"""
        try:
            unread_count = 0
            unread_channels = []
            
            conversations = self.slack_client.conversations_list(
                exclude_archived=True, 
                types='public_channel,private_channel,im'
            )
            
            for conv in conversations['channels']:
                info = self.slack_client.conversations_info(channel=conv['id'])
                unread = info['channel'].get('unlinked_count', 0)
                
                if unread > 0:
                    unread_count += unread
                    unread_channels.append({
                        'name': conv.get('name', 'Unknown'),
                        'unread': unread
                    })
            
            print(f"✓ Found {unread_count} unread Slack messages")
            return unread_count, unread_channels
            
        except SlackApiError as e:
            print(f"✗ Slack fetch failed: {e}")
            return 0, []

    def format_summary(self, events, tasks, unread_count, unread_channels):
        """Format summary as Slack message"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 Daily Summary - {datetime.now().strftime('%A, %B %d')}"
                }
            }
        ]
        
        # Calendar section
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📅 Calendar ({len(events)} events)*"
            }
        })
        
        if events:
            for event in events[:5]:
                start = event['start'].get('dateTime', event['start'].get('date'))
                title = event.get('summary', 'No title')
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"  • {title}\n    {start}"
                    }
                })
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "  No events scheduled"
                }
            })
        
        # Tasks section
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*✅ Tasks ({len(tasks)} incomplete)*"
            }
        })
        
        if tasks:
            for task in tasks[:5]:
                title = task.get('title', 'No title')
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"  • {title}"
                    }
                })
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "  All caught up! 🎉"
                }
            })
        
        # Slack unread section
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*💬 Slack Unread ({unread_count} messages)*"
            }
        })
        
        if unread_channels:
            unread_text = "\n".join([f"  • {ch['name']}: {ch['unread']} unread" for ch in unread_channels[:5]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": unread_text
                }
            })
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "  All caught up! ✨"
                }
            })
        
        return blocks

    def send_to_slack(self, blocks):
        """Send formatted summary to Slack"""
        try:
            self.slack_client.chat_postMessage(
                channel=self.slack_channel,
                blocks=blocks
            )
            print(f"✓ Summary sent to Slack channel {self.slack_channel}")
            
        except SlackApiError as e:
            print(f"✗ Failed to send to Slack: {e}")
            raise

    def run(self):
        """Run the bot"""
        print("\n🤖 Starting Daily Summary Bot...\n")
        self.authenticate_google()
        events = self.get_calendar_events()
        tasks = self.get_tasks()
        unread_count, unread_channels = self.get_slack_unread()
        blocks = self.format_summary(events, tasks, unread_count, unread_channels)
        self.send_to_slack(blocks)
        print("\n✓ Daily summary complete!\n")

if __name__ == '__main__':
    bot = DailySummaryBot()
    bot.run()
