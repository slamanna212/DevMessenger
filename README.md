# GitHub to Discord Notification Bot

This bot receives GitHub webhook notifications for new issues and forwards them to Discord channels based on issue labels. Only **bug** and **feature** issue types are supported.

## Features

- ✅ Routes GitHub issue notifications to specific Discord channels:
  - 🐛 **Bug** issues → Bug Discord channel
  - ✨ **Feature/Enhancement** issues → Feature Discord channel
- ✅ Rich Discord embeds with issue details:
  - Issue title and description
  - Repository name
  - Creator information and avatar
  - Issue type badge
  - Direct link to the issue
- ✅ Build information logging (commit hash, message, date, branch)
- ✅ Comprehensive logging and monitoring
- ✅ Health check endpoint
- ✅ Automatic Docker builds via GitHub Actions

## Setup

### Environment Variables

You only need **two** Discord webhook URLs:

```env
DISCORD_WEBHOOK_BUG=your_bug_webhook_url
DISCORD_WEBHOOK_FEATURE=your_feature_webhook_url
```

### Option 1: Using Pre-built Docker Image (Recommended)

The bot is available as a pre-built Docker image from GitHub Container Registry:

```bash
# Pull the latest image
docker pull ghcr.io/slamanna212/devmessenger:latest

# Run the container
docker run -d \
  --name github-discord-bot \
  -p 5000:5000 \
  -e DISCORD_WEBHOOK_BUG="your_bug_webhook_url" \
  -e DISCORD_WEBHOOK_FEATURE="your_feature_webhook_url" \
  --restart unless-stopped \
  ghcr.io/slamanna212/devmessenger:latest
```

### Option 2: Building Locally

1. Clone this repository:
   ```bash
   git clone https://github.com/slamanna212/DevMessenger.git
   cd DevMessenger
   ```

2. Create a `.env` file:
   ```bash
   DISCORD_WEBHOOK_BUG=your_bug_webhook_url
   DISCORD_WEBHOOK_FEATURE=your_feature_webhook_url
   ```

3. Build and run:
   ```bash
   docker build -t github-discord-bot .
   docker run -d \
     --name github-discord-bot \
     -p 5000:5000 \
     --env-file .env \
     github-discord-bot
   ```

### Option 3: Running Locally (Development)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file (see format above)

3. Run the bot:
   ```bash
   python app.py
   ```

## Discord Setup

### Creating Webhook URLs

1. **For Bug Channel:**
   - Go to your Discord server's bug reports channel
   - Click the gear icon ⚙️ next to the channel name
   - Go to "Integrations" → "Create Webhook"
   - Name it "GitHub Bug Reports" and copy the webhook URL

2. **For Feature Channel:**
   - Go to your Discord server's feature requests channel
   - Follow the same steps as above
   - Name it "GitHub Feature Requests" and copy the webhook URL

## GitHub Setup

Configure GitHub to send webhooks when issues are created and labeled:

1. Go to your GitHub repository
2. Click **"Settings"** → **"Webhooks"** → **"Add webhook"**
3. Configure:
   - **Payload URL**: `http://your-server:5000/webhook`
   - **Content type**: `application/json`
   - **Events**: Select "Let me select individual events" and choose **"Issues"**
4. Click **"Add webhook"**

## Supported Issue Types

| Issue Label | Discord Channel | Description |
|-------------|-----------------|-------------|
| `bug` | Bug webhook | Issues reporting bugs or problems |
| `feature` | Feature webhook | Feature requests and enhancements |
| `enhancement` | Feature webhook | Same as feature |
| **Other types** | ❌ **Not supported** | Returns error message |

## Build Information

The bot automatically displays build information on startup, including:
- Git commit hash and message
- Build date and branch
- Webhook configuration status

This information is **baked into the code** during Docker build, ensuring it can't be overridden by container orchestration tools.

## Monitoring and Logging

### Startup Logs
```
🔧 Webhook Configuration:
   ├─ Bug webhook: ✓ Configured
   └─ Feature webhook: ✓ Configured

📋 Build Information:
   ├─ Branch: main
   ├─ Commit: a1b2c3d4...
   ├─ Message: Add new feature
   └─ Date: 2025-01-15T14:30:25-05:00

🚀 Starting GitHub to Discord notification bot
🌐 Server listening on http://0.0.0.0:5000
```

### Runtime Logs
```
📥 Webhook: issues | ID: 12345678
📋 Issue #42 in owner/repo | Action: typed
🏷️  Processing: #42 'Bug in login system...' | Type: bug
📤 Sending → bug channel: #42 'Bug in login system...' by @username
✅ Discord → bug: Issue #42 delivered (HTTP 200)
✅ Complete: Issue #42 → Discord (HTTP 200)
```

### Viewing Logs

```bash
# View all logs
docker logs github-discord-bot

# Follow logs in real-time
docker logs -f github-discord-bot

# View last 100 lines
docker logs --tail 100 github-discord-bot
```

### Health Check

The bot provides a health check endpoint:
```bash
curl http://localhost:5000/health
# Response: {"status": "healthy"}
```

## Error Handling

### Unsupported Issue Types
When an issue is created with an unsupported label, the bot will:
- Log a warning message
- Return HTTP 400 with clear error message
- Not send any Discord notification

### Missing Webhooks
If a required webhook URL is not configured:
- Startup logs will show "✗ Not configured"
- Runtime will return appropriate error messages

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

# Update to latest version
docker pull ghcr.io/slamanna212/devmessenger:latest
docker stop github-discord-bot
docker rm github-discord-bot
# Run with new image (use your run command from setup)
```

## CI/CD Pipeline

The project includes automated GitHub Actions workflows:

### Docker Build Workflow
- **Triggers**: Push to main/dev, Pull Requests, Version tags
- **Features**:
  - Extracts git information during build
  - Builds multi-architecture Docker images
  - Pushes to GitHub Container Registry (GHCR)
  - Uses aggressive caching prevention (`no-cache: true`)

### Available Image Tags
- `latest`: Most recent build from main branch
- `main`: Same as latest
- `dev`: Development branch builds
- `v*.*.*`: Version release tags
- `sha-*`: Specific commit builds

### Using Specific Versions
```bash
# Use latest stable
docker pull ghcr.io/slamanna212/devmessenger:latest

# Use specific version
docker pull ghcr.io/slamanna212/devmessenger:v1.2.3

# Use development version
docker pull ghcr.io/slamanna212/devmessenger:dev
```

## Development

### Local Development
When running locally, the bot will show:
```
📋 Build Information: Development build (git info not available)
```

### Building with Git Information
Git information is automatically captured during Docker builds. The build process:

1. Extracts current git commit, message, date, and branch
2. Generates `build_info.py` with this information baked into the code
3. App imports build information from the generated file (not environment variables)
4. This prevents container orchestration tools from overriding build metadata

### Creating Releases
```bash
# Tag a new version
git tag v1.2.3
git push origin v1.2.3

# GitHub Actions will automatically build and push the tagged version
```

## Troubleshooting

### Common Issues

1. **"No webhook configured for this issue type"**
   - Issue was labeled with unsupported type
   - Only `bug`, `feature`, and `enhancement` are supported

2. **Webhook not receiving notifications**
   - Check GitHub webhook settings
   - Ensure your server is accessible from the internet
   - Verify webhook URL is correct

3. **Container shows old git information**
   - Ensure you're pulling the latest image: `docker pull ghcr.io/slamanna212/devmessenger:latest`
   - Check the image tag you're running

### Development Setup
For local development without Docker:
1. The `build_info.py` file provides fallback values
2. Logs will show "Development build"
3. All functionality works the same

## Network Requirements

- **Inbound**: Port 5000 (HTTP) accessible from GitHub's webhook IPs
- **Outbound**: HTTPS access to Discord's API (`discord.com`)

For local testing, consider using [ngrok](https://ngrok.com/) to expose your local server.

## License

MIT License - Feel free to modify and distribute! 