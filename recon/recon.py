import json
import asyncio
import os
import datetime
import tempfile
import subprocess
from pathlib import Path
from telegram import Bot
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === CONFIGURATION FROM ENVIRONMENT ===
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TARGETS_JSON = os.getenv('TARGETS_JSON', './targets.json')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', './output/')

# Tool paths - with fallback defaults
SUBFINDER_PATH = os.getenv('SUBFINDER_PATH', 'subfinder')
AMASS_PATH = os.getenv('AMASS_PATH', 'amass')
FINDOMAIN_PATH = os.getenv('FINDOMAIN_PATH', 'findomain')
BBOT_PATH = os.getenv('BBOT_PATH', 'bbot')

# Validate required environment variables
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is required")
if not TELEGRAM_CHAT_ID:
    raise ValueError("TELEGRAM_CHAT_ID environment variable is required")

bot = Bot(token=TELEGRAM_TOKEN)

def load_targets():
    """Load target domains from JSON file"""
    with open(TARGETS_JSON, 'r') as f:
        data = json.load(f)
    return data

def save_targets(data):
    """Save target domains to JSON file"""
    with open(TARGETS_JSON, 'w') as f:
        json.dump(data, f, indent=2)

def run_all_tools(domain):
    """Run all subdomain enumeration tools and combine results"""
    results = set()
    
    # Subfinder
    try:
        print(f"[+] Running subfinder on {domain}")
        subf = subprocess.run([SUBFINDER_PATH, '-silent', '-d', domain], 
                            capture_output=True, text=True, timeout=300)
        results.update(subf.stdout.splitlines())
    except Exception as e:
        print(f"[!] subfinder failed: {e}")
    
    # Amass
    try:
        print(f"[+] Running amass on {domain}")
        amass = subprocess.run([AMASS_PATH, 'enum', '-passive', '-norecursive', '-d', domain], 
                             capture_output=True, text=True, timeout=600)
        results.update(amass.stdout.splitlines())
    except Exception as e:
        print(f"[!] amass failed: {e}")
    
    # Findomain
    try:
        print(f"[+] Running findomain on {domain}")
        findomain = subprocess.run([FINDOMAIN_PATH, '-t', domain, '-q'], 
                                 capture_output=True, text=True, timeout=300)
        results.update(findomain.stdout.splitlines())
    except Exception as e:
        print(f"[!] findomain failed: {e}")
    
    # BBOT
    try:
        print(f"[+] Running bbot on {domain}")
        bbot_json = subprocess.run(
            ['bbot', '-t', domain, '-f', 'json'], 
            capture_output=True, text=True, timeout=600
        )
        for line in bbot_json.stdout.splitlines():
            try:
                data = json.loads(line)
                if data.get("type") == "subdomain":
                    results.add(data.get("data"))
            except Exception:
                continue
    except Exception as e:
        print(f"[!] bbot failed: {e}")
    
    # Clean and return results
    clean_results = {r.strip() for r in results if r.strip() and '.' in r}
    return clean_results

def notify_telegram(domain, new_subdomains):
    """Send new subdomains to Telegram"""
    if not new_subdomains:
        return
    
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        
        # Create a temporary text file with the new subdomains
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as tmp_file:
            tmp_file.write(f"🎯 New subdomains found for {domain}:\n\n")
            tmp_file.write("\n".join(sorted(new_subdomains)))
            tmp_file.write(f"\n\n📊 Total new subdomains: {len(new_subdomains)}")
            tmp_file.write(f"\n⏰ Scan time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            tmp_path = tmp_file.name
        
        # Send the file to Telegram
        with open(tmp_path, "rb") as f:
            bot.send_document(
                chat_id=TELEGRAM_CHAT_ID, 
                document=f, 
                filename=f"{domain}_new_subdomains_{datetime.date.today()}.txt",
                caption=f"🔍 Found {len(new_subdomains)} new subdomains for {domain}"
            )
        
        # Remove the temp file
        os.remove(tmp_path)
        print(f"[+] Notified Telegram about {len(new_subdomains)} new subdomains")
        
    except Exception as e:
        print(f"[!] Telegram notification failed: {e}")

def save_results(domain, subdomains):
    """Save scan results to files"""
    today = datetime.date.today().isoformat()
    domain_dir = os.path.join(OUTPUT_DIR, domain)
    os.makedirs(domain_dir, exist_ok=True)
    
    today_file = os.path.join(domain_dir, f'subs-{today}.txt')
    latest_file = os.path.join(domain_dir, 'latest.txt')
    
    sorted_subs = sorted(subdomains)
    
    # Save today's results
    with open(today_file, 'w') as f:
        f.write("\n".join(sorted_subs))
    
    # Update latest results
    with open(latest_file, 'w') as f:
        f.write("\n".join(sorted_subs))
    
    print(f"[+] Saved {len(subdomains)} subdomains to {today_file}")

def get_previous_subs(domain):
    """Get previously found subdomains"""
    latest_file = os.path.join(OUTPUT_DIR, domain, 'latest.txt')
    if os.path.exists(latest_file):
        with open(latest_file) as f:
            return set(line.strip() for line in f.readlines() if line.strip())
    return set()

def create_sample_targets():
    """Create a sample targets.json file"""
    sample_data = {
        "targets": [
            {
                "domain": "example.com",
                "enabled": True,
                "last_scanned": None,
                "description": "Sample target domain"
            }
        ]
    }
    
    if not os.path.exists(TARGETS_JSON):
        os.makedirs(os.path.dirname(TARGETS_JSON), exist_ok=True)
        with open(TARGETS_JSON, 'w') as f:
            json.dump(sample_data, f, indent=2)
        print(f"[+] Created sample targets file at {TARGETS_JSON}")

def main():
    """Main execution function"""
    print("🔍 Starting subdomain reconnaissance...")
    
    # Create sample targets file if it doesn't exist
    create_sample_targets()
    
    try:
        targets_data = load_targets()
    except FileNotFoundError:
        print(f"[!] Targets file not found: {TARGETS_JSON}")
        return
    except json.JSONDecodeError:
        print(f"[!] Invalid JSON in targets file: {TARGETS_JSON}")
        return
    
    if not targets_data.get('targets'):
        print("[!] No targets found in targets file")
        return
    
    for target in targets_data['targets']:
        domain = target.get('domain')
        enabled = target.get('enabled', False)
        
        if not domain:
            print("[!] Skipping target with no domain")
            continue
            
        if not enabled:
            print(f"[-] Skipping disabled target: {domain}")
            continue
        
        print(f"\n[+] Scanning {domain}...")
        
        try:
            # Run all tools and get results
            current_subs = run_all_tools(domain)
            print(f"[+] Found {len(current_subs)} total subdomains")
            
            # Get previous results
            previous_subs = get_previous_subs(domain)
            print(f"[+] Previous scan had {len(previous_subs)} subdomains")
            
            # Find new subdomains
            new_subs = current_subs - previous_subs
            
            if new_subs:
                print(f"[+] Found {len(new_subs)} new subdomains!")
                notify_telegram(domain, new_subs)
            else:
                print(f"[=] No new subdomains found for {domain}")
            
            # Save results
            save_results(domain, current_subs)
            
            # Update last_scanned timestamp
            target['last_scanned'] = datetime.datetime.utcnow().isoformat() + 'Z'
            
        except Exception as e:
            print(f"[!] Error scanning {domain}: {e}")
    
    # Save updated targets data
    try:
        save_targets(targets_data)
        print("[+] Updated targets file with scan timestamps")
    except Exception as e:
        print(f"[!] Failed to save targets: {e}")
    
    print("\n✅ Reconnaissance complete!")

if __name__ == '__main__':
    main()