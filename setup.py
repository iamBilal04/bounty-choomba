#!/usr/bin/env python3
"""
Setup script for Subdomain Recon Tool
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.6+"""
    if sys.version_info < (3, 6):
        print("❌ Python 3.6 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    dirs = ['output', 'logs']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"📁 Created directory: {dir_name}/")

def check_tools():
    """Check if recon tools are available"""
    tools = {
        'subfinder': 'https://github.com/projectdiscovery/subfinder',
        'amass': 'https://github.com/OWASP/Amass',
        'findomain': 'https://github.com/Findomain/Findomain',
        'bbot': 'https://github.com/blacklanternsecurity/bbot'
    }
    
    print("\n🔧 Checking recon tools...")
    missing_tools = []
    
    for tool, url in tools.items():
        if shutil.which(tool):
            print(f"✅ {tool} found")
        else:
            print(f"❌ {tool} not found - Install from: {url}")
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"\n⚠️  Missing tools: {', '.join(missing_tools)}")
        print("Install them manually or the script will skip those tools during scanning")

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        print("\n📝 Creating .env template...")
        with open('.env.template', 'r') as template:
            content = template.read()
        with open('.env', 'w') as env_file:
            env_file.write(content)
        print("✅ Created .env file")
        print("⚠️  IMPORTANT: Edit .env file with your Telegram bot token and chat ID!")
    else:
        print("✅ .env file already exists")

def create_sample_targets():
    """Create sample targets.json if it doesn't exist"""
    if not os.path.exists('targets.json'):
        print("📋 Creating sample targets.json...")
        sample_data = {
            "targets": [
                {
                    "domain": "example.com",
                    "enabled": false,
                    "description": "Sample domain - change this to your target",
                    "priority": "medium"
                }
            ],
            "config": {
                "notification_enabled": true,
                "scan_timeout": 300
            }
        }
        import json
        with open('targets.json', 'w') as f:
            json.dump(sample_data, f, indent=2)
        print("✅ Created sample targets.json")
        print("⚠️  Edit targets.json to add your actual target domains")

def main():
    """Main setup function"""
    print("🚀 Setting up Subdomain Recon Tool...\n")
    
    check_python_version()
    install_requirements()
    create_directories() 
    check_tools()
    create_env_file()
    create_sample_targets()
    
    print("\n" + "="*50)
    print("✅ Setup complete!")
    print("\n📝 Next steps:")
    print("1. Edit .env file with your Telegram credentials")
    print("2. Edit targets.json with your target domains")
    print("3. Run: python recon.py")
    print("\n🔧 Install missing recon tools as needed")
    print("="*50)

if __name__ == "__main__":
    main()