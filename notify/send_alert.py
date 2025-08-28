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

def notify_telegram(domain, new_subdomains):
    """Send new subdomains to Telegram as a text file"""
    import tempfile
    if not new_subdomains:
        print("[!] No new subdomains to send.")
        return
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"{domain}_new_subdomains_{timestamp}.txt"
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt", encoding='utf-8') as tmp_file:
            tmp_file.write(f"🎯 NEW SUBDOMAINS DISCOVERED\n")
            tmp_file.write(f"Domain: {domain}\n")
            tmp_file.write(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            tmp_file.write(f"Total New Subdomains: {len(new_subdomains)}\n")
            tmp_file.write("=" * 50 + "\n\n")
            for subdomain in sorted(new_subdomains):
                tmp_file.write(f"{subdomain}\n")
            tmp_file.write(f"\n" + "=" * 50 + "\n")
            tmp_file.write(f"End of report - {len(new_subdomains)} subdomains found\n")
            tmp_path = tmp_file.name
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        with open(tmp_path, "rb") as f:
            files = {
                'document': (filename, f, 'text/plain')
            }
            data = {
                'chat_id': CHAT_ID,
                'caption': f"🔍 Found {len(new_subdomains)} new subdomains for {domain}\n📅 Scan: {timestamp}"
            }
            response = requests.post(url, files=files, data=data, timeout=30)
            response.raise_for_status()
        os.remove(tmp_path)
        print(f"[+] Sent file with {len(new_subdomains)} new subdomains to Telegram")
    except Exception as e:
        print(f"[!] Telegram file upload failed: {e}")
        try:
            fallback_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            fallback_message = f"🎯 Found {len(new_subdomains)} new subdomains for {domain}\n⚠️ File upload failed, but scan completed successfully!"
            requests.post(fallback_url, data={
                "chat_id": CHAT_ID, 
                "text": fallback_message
            }, timeout=10)
            print(f"[+] Sent fallback message to Telegram")
        except Exception as fallback_error:
            print(f"[!] Fallback message also failed: {fallback_error}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python send_alert.py <message> [level]")
        print("  python send_alert.py --domain example.com --subdomains sub1,sub2,sub3")
        print("Levels: INFO, WARNING, ERROR, SUCCESS, ALERT")
        sys.exit(1)

    # Support: python send_alert.py --domain example.com --subdomains sub1,sub2,sub3
    if '--domain' in sys.argv and '--subdomains' in sys.argv:
        try:
            domain_idx = sys.argv.index('--domain') + 1
            subdomains_idx = sys.argv.index('--subdomains') + 1
            domain = sys.argv[domain_idx]
            subdomains_raw = sys.argv[subdomains_idx]
            new_subdomains = [s.strip() for s in subdomains_raw.split(',') if s.strip()]
            notify_telegram(domain, new_subdomains)
            return
        except Exception as e:
            print(f"[!] Error parsing arguments: {e}")
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