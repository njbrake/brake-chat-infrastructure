# Home Server Stack

Docker Compose stack for home server services including Jellyfin, OpenWebUI, and ngrok.

## Services

- **Jellyfin**: Media server (port 8096)
- **OpenWebUI**: Web interface for AI models (port 3000)
- **ngrok**: Tunnel service for external access to Jellyfin

## Environment Variables

Before running the stack, you need to set the following environment variables:

### Required Variables

- `NGROK_AUTHTOKEN`: Your ngrok authentication token
  - Get this from [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)
  - Required for ngrok tunnel functionality

### Optional Variables

- `OLLAMA_BASE_URL`: URL of your Ollama instance (default: `http://host.docker.internal:11434`)
  - Set this if your Ollama is running on a different host/port
  - Examples:
    - `http://192.168.1.100:11434` (remote host)
    - `http://localhost:11434` (local host)

### OpenWebUI Variables

- `WEBUI_URL`: Public URL for OpenWebUI (required for OAuth)
- `WEBUI_SECRET_KEY`: Secret key for session management
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `ENABLE_OAUTH_SIGNUP`: Enable OAuth signup (default: `true`)

### Jellyfin Variables

- `MEDIA_PATH`: Path to your media files on the host system (default: `/media`)
  - Examples:
    - `/mnt/external-drive/media` (external hard drive)
    - `/home/user/Movies` (local directory)
    - `/Volumes/MyDrive/Movies` (macOS external drive)

## Quick Start

1. Create a `.env` file in the project root with the following content:
   ```env
   # Required
   NGROK_AUTHTOKEN=your_ngrok_token_here
   
   # Optional - Ollama Configuration
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   
   # Optional - OpenWebUI Configuration
   WEBUI_URL=https://your-domain.com
   WEBUI_SECRET_KEY=your_secret_key_here
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ENABLE_OAUTH_SIGNUP=true
   
   # Optional - Jellyfin Configuration
   MEDIA_PATH=/path/to/your/media
   ```

2. Edit the `.env` file with your actual values

3. Start the services:
   ```bash
   docker-compose up -d
   ```

## Access Points

- **Jellyfin**: http://localhost:8096
- **OpenWebUI**: http://localhost:3000
- **ngrok tunnel**: Check ngrok dashboard for public URL

## Prerequisites

- Docker and Docker Compose installed
- Ollama running separately (not managed by this compose file)
- ngrok account and auth token
