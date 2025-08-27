#!/bin/bash
# Cron Setup Script for Subdomain Recon Tool (Fixed for your directory structure)

echo "🕒 Setting up cron jobs for automated subdomain reconnaissance..."

# Get the current directory (where the scripts are located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Script directory: $SCRIPT_DIR"

# Create a wrapper script for cron (cron has limited environment)
cat > "$SCRIPT_DIR/run_recon.sh" << EOF
#!/bin/bash
# Cron wrapper script for recon.py - Fixed for your directory structure

# Set PATH to include common binary locations
export PATH="/usr/local/bin:/usr/bin:/bin:/home/ec2-user/go/bin:/home/ec2-user/.local/bin:\$PATH"

# Change to script directory
cd "$SCRIPT_DIR"

# Log file for cron output
LOG_FILE="$SCRIPT_DIR/logs/cron_recon.log"

# Create log directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Run the recon script with logging (note: recon.py is in recon/ subdirectory)
echo "=== Cron job started at \$(date) ===" >> "\$LOG_FILE"
cd "$SCRIPT_DIR/recon" && python3 recon.py >> "\$LOG_FILE" 2>&1
echo "=== Cron job finished at \$(date) ===" >> "\$LOG_FILE"
echo "" >> "\$LOG_FILE"

# Send completion notification (note: send_alert.py is in notify/ subdirectory)
cd "$SCRIPT_DIR/notify" && python3 send_alert.py "🤖 Scheduled recon scan completed" INFO >> "\$LOG_FILE" 2>&1
EOF

# Make the wrapper script executable
chmod +x "$SCRIPT_DIR/run_recon.sh"
echo "✅ Created wrapper script: $SCRIPT_DIR/run_recon.sh"

# Show current crontab
echo ""
echo "📋 Current crontab entries:"
crontab -l 2>/dev/null || echo "No current crontab entries"

echo ""
echo "🔧 Suggested cron job entries:"
echo "# Add one of these to your crontab using: crontab -e"
echo ""
echo "# Run every 6 hours"
echo "0 */6 * * * $SCRIPT_DIR/run_recon.sh"
echo ""
echo "# Run daily at 2 AM"
echo "0 2 * * * $SCRIPT_DIR/run_recon.sh"
echo ""
echo "# Run every 2 hours (more frequent)"
echo "0 */2 * * * $SCRIPT_DIR/run_recon.sh"
echo ""
echo "# Run twice daily (8 AM and 8 PM)"
echo "0 8,20 * * * $SCRIPT_DIR/run_recon.sh"

echo ""
echo "📝 To set up cron job:"
echo "1. Run: crontab -e"
echo "2. Add one of the above lines"
echo "3. Save and exit"
echo ""
echo "🔍 To monitor cron jobs:"
echo "- View logs: tail -f $SCRIPT_DIR/logs/cron_recon.log"
echo "- Check cron status: systemctl status crond"
echo "- List active crons: crontab -l"