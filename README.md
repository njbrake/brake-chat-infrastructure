# Home Server Stack

Deploy a OpenWebUI server on your own hardware, expose it securely to the web via Cloudflare tunnels, and secure it
with Google OAuth. See `docker-compose.yml` for the stack and variables.

## Environment Variables

Read the `.env.example` file to see what environment variables should be set: you'll see that the `docker-compose.yml` file
loads those env vars (when they're in a `.env` file)

## Quick Start

1. Create a `.env` file by copying the `.env.example` file
    ```bash
    cp .env.example .env
    ```
2. Edit the `.env` file with your actual values.
3. Start the services:
    ```bash
    docker compose up -d
    ```
4. Monitor the logs:
    ```bash
    docker compose logs -f
    ```

## Access Points

- **OpenWebUI**: http://localhost:3000
- **cloudflare tunnel**: Exposed to whatever you configured in cloudflare and the env var

## Prerequisites

- Docker and Docker Compose installed
- cloudflare account and auth token
