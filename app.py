import os
import logging
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Discord webhook URLs
DISCORD_WEBHOOK_BUG = os.getenv('DISCORD_WEBHOOK_BUG')
DISCORD_WEBHOOK_FEATURE = os.getenv('DISCORD_WEBHOOK_FEATURE')
DISCORD_WEBHOOK_DEFAULT = os.getenv('DISCORD_WEBHOOK_DEFAULT')

def get_webhook_url(issue_type):
    """Determine which Discord webhook URL to use based on issue type"""
    if not issue_type:
        logger.info(f"No type provided, using default webhook")
        return DISCORD_WEBHOOK_DEFAULT
    
    type_name = issue_type['name'].lower()
    
    if type_name == 'bug':
        logger.info(f"Issue typed as bug, using bug webhook")
        return DISCORD_WEBHOOK_BUG
    elif type_name == 'feature' or type_name == 'enhancement':
        logger.info(f"Issue typed as feature/enhancement, using feature webhook")
        return DISCORD_WEBHOOK_FEATURE
    
    logger.info(f"Type {type_name} not matched, using default webhook")
    return DISCORD_WEBHOOK_DEFAULT

def send_discord_notification(webhook_url, issue_data):
    """Send notification to Discord"""
    if not webhook_url:
        logger.error("No webhook URL provided")
        return
    
    # Extract relevant information
    issue = issue_data['issue']
    repo = issue_data['repository']
    user = issue['user']
    issue_type = issue_data.get('type', {})
    
    logger.info(f"Preparing Discord notification for issue: {issue['title']} in repo: {repo['full_name']}")
    
    # Create Discord embed
    embed = {
        "title": f"New Issue: {issue['title']}",
        "description": issue['body'][:2000] if issue['body'] else "No description provided",
        "url": issue['html_url'],
        "color": 5814783,  # Blue color
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
    try:
        logger.info(f"Sending notification to Discord webhook")
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        logger.info(f"Successfully sent notification to Discord. Status code: {response.status_code}")
        return response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Discord notification: {str(e)}")
        return None

@app.route('/webhook', methods=['POST'])
def github_webhook():
    """Handle incoming GitHub webhooks"""
    # Log headers for debugging
    event_type = request.headers.get('X-GitHub-Event')
    delivery_id = request.headers.get('X-GitHub-Delivery')
    logger.info(f"Received GitHub webhook - Event: {event_type}, Delivery ID: {delivery_id}")
    
    data = request.json
    
    # Only process issue events
    if event_type != 'issues':
        logger.info(f"Skipping non-issue event: {event_type}")
        return jsonify({"message": "Not an issue event"}), 200
        
    # Only process when issues are typed
    if data['action'] != 'typed':
        logger.info(f"Skipping issue event with action: {data['action']}")
        return jsonify({"message": "Not an issue typing event"}), 200
    
    issue_number = data['issue']['number']
    repo_name = data['repository']['full_name']
    logger.info(f"Processing typed issue #{issue_number} from {repo_name}")
    
    # Get appropriate webhook URL based on type
    webhook_url = get_webhook_url(data.get('type'))
    
    # Send notification
    status_code = send_discord_notification(webhook_url, data)
    
    response_message = {
        "message": "Notification sent" if status_code else "Failed to send notification",
        "status_code": status_code,
        "issue_number": issue_number,
        "repository": repo_name
    }
    
    logger.info(f"Webhook processing complete: {response_message}")
    return jsonify(response_message), 200 if status_code else 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    logger.info("Health check requested")
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    logger.info("Starting GitHub to Discord notification bot")
    app.run(host='0.0.0.0', port=5000)