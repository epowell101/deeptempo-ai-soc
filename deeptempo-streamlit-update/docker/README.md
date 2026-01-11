# Docker Setup for DeepTempo AI SOC

This directory contains Docker Compose configuration to run a local Timesketch instance for timeline visualization of DeepTempo LogLM findings.

## Prerequisites

- Docker Desktop (Mac/Windows) or Docker Engine (Linux)
- At least **8GB RAM** available for Docker
- Docker Compose v2+

## Quick Start

```bash
# Start all services
cd docker
docker compose up -d

# Wait for services to be healthy (2-3 minutes)
docker compose ps

# Check logs if needed
docker compose logs -f timesketch
```

## Access

| Service | URL | Credentials |
|---------|-----|-------------|
| Timesketch UI | http://localhost:5000 | dev / dev |
| OpenSearch | http://localhost:9200 | N/A |

## Services

| Service | Purpose | Port |
|---------|---------|------|
| `timesketch` | Main Timesketch web application | 5000 |
| `timesketch-worker` | Background task processing | - |
| `opensearch` | Search and indexing backend | 9200 |
| `postgres` | Database for Timesketch metadata | 5432 |
| `redis` | Message broker for async tasks | 6379 |

## Usage with DeepTempo AI SOC

Once Timesketch is running, configure the MCP server to connect:

```bash
# Set environment variables (optional - defaults to localhost)
export TIMESKETCH_HOST=http://localhost:5000
export TIMESKETCH_USER=dev
export TIMESKETCH_PASSWORD=dev
export TIMESKETCH_MOCK=false  # Use real Timesketch instead of mock mode
```

Or update the Claude Desktop config:

```json
{
  "mcpServers": {
    "timesketch": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "mcp_servers.timesketch_server.server"],
      "cwd": "/path/to/deeptempo-ai-soc",
      "env": {
        "PYTHONPATH": "/path/to/deeptempo-ai-soc",
        "TIMESKETCH_HOST": "http://localhost:5000",
        "TIMESKETCH_USER": "dev",
        "TIMESKETCH_PASSWORD": "dev",
        "TIMESKETCH_MOCK": "false"
      }
    }
  }
}
```

## Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Stop and remove all data
docker compose down -v

# View logs
docker compose logs -f

# Restart a specific service
docker compose restart timesketch

# Check service health
docker compose ps
```

## Troubleshooting

### Services won't start
- Ensure Docker has at least 8GB RAM allocated
- Check if ports 5000, 9200 are available
- Run `docker compose logs` to see error messages

### Timesketch is slow to start
- First startup can take 2-3 minutes
- OpenSearch needs time to initialize
- Check health with `docker compose ps`

### Can't connect from MCP server
- Verify Timesketch is healthy: `curl http://localhost:5000/login`
- Check firewall settings
- Ensure `TIMESKETCH_MOCK=false` is set

### Reset everything
```bash
docker compose down -v
docker compose up -d
```

## Resource Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 8GB | 16GB |
| CPU | 2 cores | 4 cores |
| Disk | 10GB | 50GB |

## Production Notes

For production deployments:

1. Change `SECRET_KEY` to a secure random value
2. Use proper passwords for PostgreSQL
3. Enable OpenSearch security features
4. Set up HTTPS/TLS
5. Configure proper backup for volumes

See the [official Timesketch documentation](https://timesketch.org/guides/admin/install/) for production deployment guidance.
