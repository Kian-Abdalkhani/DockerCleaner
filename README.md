# Homeserver Scripts

A Docker management application that runs scheduled tasks for Docker cleanup and container stack restarts.

## Features

- Automated Docker system cleanup (Mondays at 3:00am)
- Automated restart of all running Docker Compose stacks (Mondays at 4:00am)
- Self-exclusion: Prevents restarting its own Docker Compose stack
- Logging with rotation
- Containerized deployment

## Docker Deployment

### Prerequisites

- Docker and Docker Compose installed on the host system
- The container needs access to the Docker socket to manage other containers

### Quick Start

1. Build and run using Docker Compose:
```bash
docker-compose up -d
```

2. View logs:
```bash
docker-compose logs -f homeserver-scripts
```

3. Stop the service:
```bash
docker-compose down
```

### Manual Docker Build

If you prefer to build manually:

```bash
# Build the image
docker build -t homeserver-scripts .

# Run the container
docker run -d \
  --name homeserver-scripts \
  --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ./logs:/app/logs \
  homeserver-scripts
```

## Configuration

The application runs scheduled tasks:
- **Monday 03:00**: Docker system cleanup (`docker system prune -f`)
- **Monday 04:00**: Restart all running Docker Compose stacks (excluding self)

Logs are stored in the `logs/` directory and rotated when they reach 1MB.

### Self-Exclusion from Restarts

To prevent the script from restarting its own Docker Compose stack (which would cause interruption), the application automatically excludes certain stacks from restart operations:

- **Default exclusion**: The stack named `homeserver-scripts` (matching the default service name)
- **Environment variable**: Any stack name specified in the `COMPOSE_PROJECT_NAME` environment variable

#### Customizing Excluded Stacks

If you're using a different project name for this stack, you can:

1. **Set the environment variable** in your docker-compose.yml:
```yaml
environment:
  - COMPOSE_PROJECT_NAME=your-custom-stack-name
```

2. **Or modify the EXCLUDED_STACKS list** in `scripts/main.py`:
```python
EXCLUDED_STACKS = [
    "homeserver-scripts",
    "your-custom-stack-name",
    os.getenv("COMPOSE_PROJECT_NAME", ""),
]
```

The application will log which stacks are being excluded during each restart cycle.

## Security Notes

- The container runs as root to access the Docker socket
- The Docker socket is mounted to allow container management
- Only use this in trusted environments as it has elevated Docker privileges
