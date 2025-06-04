# GitHub to Discord Notification Bot

This bot receives GitHub webhook notifications for new issues and forwards them to different Discord channels based on the issue labels.

## Setup

### Option 1: Running with Docker (Recommended)

#### Using Pre-built Image

The bot is available as a pre-built Docker image from GitHub Container Registry:
```bash
docker pull ghcr.io/OWNER/github-discord-bot:latest
```
Replace `OWNER` with your GitHub username.

#### Building Locally

1. Create a `.env` file based on these environment variables:
   ```
   DISCORD_WEBHOOK_BUG=your_webhook_url_for_bugs
   DISCORD_WEBHOOK_FEATURE=your_webhook_url_for_features
   DISCORD_WEBHOOK_DEFAULT=your_webhook_url_for_other_issues
   ```

2. Build the Docker image:
   ```bash
   docker build -t github-discord-bot .
   ```

3. Run the container:
   ```bash
   docker run -d \
     --name github-discord-bot \
     -p 5000:5000 \
     --env-file .env \
     github-discord-bot
   ```

### Option 2: Running Locally

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file (see format above)

4. Run the bot:
   ```bash
   python app.py
   ```

## Monitoring and Logging

The bot provides comprehensive logging for all GitHub webhook receipts and Discord message sends.

### Viewing Logs

#### Docker Logs
```bash
# View all logs
docker logs github-discord-bot

# Follow logs in real-time
docker logs -f github-discord-bot
```

#### Local Logs
When running locally, logs are printed to stdout.

### Log Format
Logs include timestamps and detailed information about each event:
```
2024-02-20 10:15:23 - INFO - Starting GitHub to Discord notification bot
2024-02-20 10:15:45 - INFO - Received GitHub webhook - Event: issues, Delivery ID: 123e4567-e89b-12d3-a456-426614174000
2024-02-20 10:15:45 - INFO - Processing new issue #42 from user/repo
2024-02-20 10:15:45 - INFO - Issue labeled as bug, using bug webhook
2024-02-20 10:15:45 - INFO - Preparing Discord notification for issue: Bug Report in repo: user/repo
2024-02-20 10:15:46 - INFO - Successfully sent notification to Discord. Status code: 200
```

### Health Check
The bot provides a health check endpoint at `/health`:
```bash
curl http://localhost:5000/health
```

### What's Being Logged
- GitHub webhook receipts (with event type and delivery ID)
- Issue processing (issue number and repository)
- Label detection and webhook selection
- Discord notification preparation and sending
- Success/failure of Discord message delivery
- Application startup and health checks

## Discord Setup

1. Get Discord webhook URLs:
   - In Discord, go to the channel where you want to receive notifications
   - Click the gear icon ⚙️ next to the channel name
   - Go to "Integrations" > "Create Webhook"
   - Give it a name and copy the webhook URL
   - Repeat for each channel type (bug, feature, default)

## GitHub Setup

1. Configure GitHub webhooks:
   - Go to your GitHub repository
   - Click "Settings" > "Webhooks" > "Add webhook"
   - Set Payload URL to: `http://your-server:5000/webhook`
   - Content type: `application/json`
   - Select "Let me select individual events" and choose only "Issues"
   - Click "Add webhook"

## Features

- Receives GitHub webhook notifications for new issues
- Routes notifications to different Discord channels based on issue labels:
  - Issues labeled "bug" go to the bug channel
  - Issues labeled "feature" or "enhancement" go to the feature channel
  - All other issues go to the default channel
- Rich Discord embeds with issue details, including:
  - Issue title and description
  - Repository name
  - Creator information
  - Issue labels
  - Direct link to the issue
- Comprehensive logging and monitoring

## Docker Commands Reference

```bash
# View logs
docker logs github-discord-bot

# Follow logs in real-time
docker logs -f github-discord-bot

# Stop the container
docker stop github-discord-bot

# Remove the container
docker rm github-discord-bot

# Restart the container
docker restart github-discord-bot
```

## Note

Make sure your server is accessible from the internet so GitHub can send webhook notifications. You might need to set up port forwarding or use a service like ngrok for testing.

## CI/CD

The project includes a GitHub Actions workflow that automatically:
- Builds the Docker image for all pull requests
- Builds and pushes the image to GitHub Container Registry (GHCR) for:
  - Pushes to main branch
  - New version tags (v*.*.*)

### Available Tags
- `latest`: Most recent build from main
- `vX.Y.Z`: Specific version releases
- `vX.Y`: Latest minor version
- `sha-XXXXXXX`: Specific commit builds

### Using GitHub Container Registry
1. Authenticate with GHCR:
   ```bash
   docker login ghcr.io -u USERNAME
   ```

2. Pull the image:
   ```bash
   docker pull ghcr.io/OWNER/github-discord-bot:latest
   ```

3. Run with your environment file:
   ```bash
   docker run -d \
     --name github-discord-bot \
     -p 5000:5000 \
     --env-file .env \
     ghcr.io/OWNER/github-discord-bot:latest
   ```

### Creating Releases
To create a new version:
1. Tag your release:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
2. The workflow will automatically build and push the tagged version. 