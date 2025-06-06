import os
import logging
import sys
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

# Configure enhanced logging
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'ENDC': '\033[0m',      # End color
        'BOLD': '\033[1m',      # Bold
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{self.COLORS['BOLD']}{record.levelname:<8}{self.COLORS['ENDC']}"
        
        # Format the message
        formatted = super().format(record)
        return formatted

# Setup logging
log_formatter = ColoredFormatter(
    fmt='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Remove default handlers
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Add colored console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

# Create app logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Reduce Flask's built-in logging verbosity
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Discord webhook URLs
DISCORD_WEBHOOK_BUG = os.getenv('DISCORD_WEBHOOK_BUG')
DISCORD_WEBHOOK_FEATURE = os.getenv('DISCORD_WEBHOOK_FEATURE')
DISCORD_WEBHOOK_DEFAULT = os.getenv('DISCORD_WEBHOOK_DEFAULT')

# Log webhook configuration status
logger.info("🔧 Webhook Configuration:")
logger.info(f"   ├─ Bug webhook: {'✓ Configured' if DISCORD_WEBHOOK_BUG else '✗ Not configured'}")
logger.info(f"   ├─ Feature webhook: {'✓ Configured' if DISCORD_WEBHOOK_FEATURE else '✗ Not configured'}")
logger.info(f"   └─ Default webhook: {'✓ Configured' if DISCORD_WEBHOOK_DEFAULT else '✗ Not configured'}")

# Display build information
build_commit = os.getenv('BUILD_COMMIT_HASH', 'unknown')
build_message = os.getenv('BUILD_COMMIT_MESSAGE', 'unknown') 
build_date = os.getenv('BUILD_COMMIT_DATE', 'unknown')
build_branch = os.getenv('BUILD_BRANCH', 'unknown')

if build_commit != 'unknown':
    logger.info("📋 Build Information:")
    logger.info(f"   ├─ Branch: {build_branch}")
    logger.info(f"   ├─ Commit: {build_commit[:8]}...")
    logger.info(f"   ├─ Message: {build_message}")
    logger.info(f"   └─ Date: {build_date}")
else:
    logger.info("📋 Build Information: Development build (git info not available)")

def get_webhook_url(issue_type):
    """Determine which Discord webhook URL to use based on issue type"""
    if not issue_type:
        logger.debug("No issue type provided, using default webhook")
        return DISCORD_WEBHOOK_DEFAULT
    
    type_name = issue_type['name'].lower()
    logger.debug(f"Issue categorized as: {type_name}")
    
    if type_name == 'bug':
        logger.debug("🐛 Routing to bug webhook")
        return DISCORD_WEBHOOK_BUG
    elif type_name == 'feature' or type_name == 'enhancement':
        logger.debug("✨ Routing to feature webhook")
        return DISCORD_WEBHOOK_FEATURE
    
    logger.debug(f"🔀 Type '{type_name}' not matched, using default webhook")
    return DISCORD_WEBHOOK_DEFAULT

def send_discord_notification(webhook_url, issue_data):
    """Send notification to Discord"""
    if not webhook_url:
        logger.error("❌ No webhook URL configured")
        return
    
    try:
        # Extract relevant information
        issue = issue_data['issue']
        repo = issue_data['repository']
        user = issue['user']
        issue_type = issue_data.get('type', {})
        
        # Determine webhook type for logging
        webhook_type = "default"
        if webhook_url == DISCORD_WEBHOOK_BUG:
            webhook_type = "bug"
        elif webhook_url == DISCORD_WEBHOOK_FEATURE:
            webhook_type = "feature"
        
        logger.info(f"📤 Sending → {webhook_type} channel: #{issue['number']} '{issue['title'][:30]}...' by @{user['login']}")
        
        # Create Discord embed
        embed = {
            "title": f"New Issue: {issue['title']}",
            "description": issue['body'][:2000] if issue['body'] else "No description provided",
            "url": issue['html_url'],
            "color": int('2a84f8', 16) if issue_type.get('name', '').lower() == 'feature' else int('f8412d', 16) if issue_type.get('name', '').lower() == 'bug' else 5814783,  # Blue for feature, Red for bug, Default blue for others
            "fields": [
                {
                    "name": "Repository",
                    "value": repo['full_name'],
                    "inline": True
                },
                {
                    "name": "Created by",
                    "value": user['login'],
                    "inline": True
                },
                {
                    "name": "Type",
                    "value": issue_type.get('name', 'Unspecified'),
                    "inline": True
                }
            ],
            "thumbnail": {
                "url": user['avatar_url']
            }
        }
        
        # Prepare the payload
        payload = {
            "embeds": [embed]
        }
        
        # Send to Discord
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        
        logger.info(f"✅ Discord → {webhook_type}: Issue #{issue['number']} delivered (HTTP {response.status_code})")
        return response.status_code
        
    except KeyError as e:
        logger.error(f"❌ Data error: Missing key '{str(e)}' in webhook payload")
        logger.debug(f"Available data keys: {list(issue_data.keys())}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Discord API error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error in notification handler: {str(e)}")
        return None

@app.route('/webhook', methods=['POST'])
def github_webhook():
    """Handle incoming GitHub webhooks"""
    try:
        # Extract headers
        event_type = request.headers.get('X-GitHub-Event')
        delivery_id = request.headers.get('X-GitHub-Delivery')
        
        # Log ALL incoming webhooks for visibility
        logger.info(f"📥 Webhook: {event_type} | ID: {delivery_id[:8] if delivery_id else 'unknown'}")
        
        if not request.is_json:
            logger.warning("⚠️  Invalid payload: Not JSON")
            return jsonify({"message": "Content type must be application/json"}), 415
        
        data = request.json
        action = data.get('action')
        
        # Log the action for all webhooks
        if event_type == 'issues':
            issue_number = data.get('issue', {}).get('number', 'unknown')
            repo_name = data.get('repository', {}).get('full_name', 'unknown')
            logger.info(f"📋 Issue #{issue_number} in {repo_name} | Action: {action}")
        else:
            logger.info(f"🔄 Event: {event_type} | Action: {action} | Skipped (not issue)")
            return jsonify({"message": "Not an issue event"}), 200
            
        # Only process when issues are typed
        if action != 'typed':
            logger.info(f"⏭️  Issue action '{action}' ignored (waiting for 'typed')")
            return jsonify({"message": "Not an issue typing event"}), 200
        
        # Process the typed issue
        issue_number = data['issue']['number']
        repo_name = data['repository']['full_name']
        issue_title = data['issue']['title']
        issue_type = data.get('type', {}).get('name', 'unspecified')
        
        logger.info(f"🏷️  Processing: #{issue_number} '{issue_title[:50]}...' | Type: {issue_type}")
        
        # Get appropriate webhook URL based on type
        webhook_url = get_webhook_url(data.get('type'))
        
        # Send notification
        status_code = send_discord_notification(webhook_url, data)
        
        if status_code:
            logger.info(f"✅ Complete: Issue #{issue_number} → Discord (HTTP {status_code})")
            response_message = {
                "message": "Notification sent successfully",
                "status_code": status_code,
                "issue_number": issue_number,
                "repository": repo_name
            }
            return jsonify(response_message), 200
        else:
            logger.error(f"❌ Failed: Issue #{issue_number} → Discord notification failed")
            response_message = {
                "message": "Failed to send notification",
                "issue_number": issue_number,
                "repository": repo_name
            }
            return jsonify(response_message), 500
        
    except Exception as e:
        logger.error(f"❌ Critical error processing webhook: {str(e)}")
        return jsonify({"message": "Internal server error", "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    # No logging for health checks to reduce noise
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    logger.info("🚀 Starting GitHub to Discord notification bot")
    logger.info("🌐 Server listening on http://0.0.0.0:5000")
    
    app.run(host='0.0.0.0', port=5000)