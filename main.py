#!/usr/bin/env python3
"""
Daily Summary Bot - Slack Only Test
"""

import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class DailySummaryBot:
    def __init__(self):
        self.slack_token = os.getenv('SLACK_BOT_TOKEN')
        self.slack_channel = os.getenv('SLACK_CHANNEL_ID')
        
        if not self.slack_token or not self.slack_channel:
            raise ValueError("Missing SLACK_BOT_TOKEN or SLACK_CHANNEL_ID environment variables")
        
        self.slack_client = WebClient(token=self.slack_token)

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

    def format_summary(self, unread_count, unread_channels):
        """Format summary as Slack message"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "💬 Slack Unread Messages Test"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Total Unread: {unread_count} messages*"
                }
            }
        ]
        
        if unread_channels:
            unread_text = "\n".join([f"  • {ch['name']}: {ch['unread']} unread" for ch in unread_channels])
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
                    "text": "All caught up! ✨"
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
        print("\n🤖 Testing Slack Only...\n")
        unread_count, unread_channels = self.get_slack_unread()
        blocks = self.format_summary(unread_count, unread_channels)
        self.send_to_slack(blocks)
        print("\n✓ Slack test complete!\n")

if __name__ == '__main__':
    bot = DailySummaryBot()
    bot.run()