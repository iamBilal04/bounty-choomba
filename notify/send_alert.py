#!/usr/bin/env python3
"""
Simple Telegram alert script
Usage: python send_alert.py "Your message here"
"""

import sys
import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Validate required environment variables
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is required")
if not CHAT_ID:
    raise ValueError("TELEGRAM_CHAT_ID environment variable is required")

def send_message(message, parse_mode=None):
    """Send a message to Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    
    if parse_mode:
        payload["parse_mode"] = parse_mode
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        print(f"✅ Message sent successfully")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send message: {e}")
        return False

def send_formatted_alert(title, message, level="INFO"):
    """Send a formatted alert message"""
    emoji_map = {
        "INFO": "ℹ️",
        "WARNING": "⚠️", 
        "ERROR": "❌",
        "SUCCESS": "✅",
        "ALERT": "🚨"
    }
    
    emoji = emoji_map.get(level.upper(), "📢")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    formatted_message = f"{emoji} *{level}*\n"
    formatted_message += f"📋 *{title}*\n"
    formatted_message += f"⏰ {timestamp}\n"
    formatted_message += f"💬 {message}"
    
    return send_message(formatted_message, parse_mode="Markdown")

def main():
    if len(sys.argv) < 2:
        print("Usage: python send_alert.py <message> [level]")
        print("Levels: INFO, WARNING, ERROR, SUCCESS, ALERT")
        sys.exit(1)
    
    message = sys.argv[1]
    level = sys.argv[2] if len(sys.argv) > 2 else "INFO"
    
    # If message looks like a simple string, send it directly
    if level == "INFO" and len(sys.argv) == 2:
        send_message(message)
    else:
        send_formatted_alert("System Alert", message, level)

if __name__ == "__main__":
    main()