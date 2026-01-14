# Overview
DevContainers provide a consistent development environment  with debuggers that eliminates the need for local setup of dependencies, databases, and services. This guide will help you set up BuffaLogs backend development environment using DevContainers.

## Prerequisites
Before starting, ensure you have:
- [Visual Studio Code](https://code.visualstudio.com/) (or any other IDE which support the Dev Containers) installed
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) installed in your IDE
- Docker and Docker compose installed and running

# Quick Start
1. **Clone the repository**
   ```bash
   git clone https://github.com/certego/BuffaLogs.git
   cd BuffaLogs
   ```

2. **Open in DevContainer**
   - Open the project in VS Code
   - Before starting development with dev containers, ensure that no `buffalogs` containers are currently running on your system. This prevents port conflicts and any errors that could interfere with the dev container environment.
   - To see current docker containers running on your system, execute: `docker ps`. There shouldn't be any running containers.
   - Press `Ctrl+Shift+P`
   - Select or type "Dev Containers: Reopen in Container"
   - Wait for the container to build and start (first time may take few minutes)

3. **Verify setup**
   The DevContainer will automatically build and run following containers:
   - PostgreSQL database
   - RabbitMQ message broker
   - Celery and Celery beat workers
   - Run Django migrations
   - Runs `debugpy` on port `5678` for debugging
   - Start the Django development server on port 8000

# Development Environment
The DevContainer provides the following services:

## Core Services
| **Service** | **Port** | **Description** | **Access** |
|---|---|---|---|
| Django Dev Server | 8000 | Main BuffaLogs application | http://localhost:8000 |
| PostgreSQL | 5433 | Primary database | localhost:5433 |
| RabbitMQ | 5672 | Message broker | localhost:5672 |
| RabbitMQ Management | 15672 | Web management UI | http://localhost:15672 |
| Celery Worker | 5679 | Celery Worker debugging | localhost:5679 |
| Debug Server | 5678 | Python debugging | localhost:5678 |

## Development Tools
The container includes:
- **Python 3.12** with all BuffaLogs dependencies
- **Django Debug Toolbar** for enhanced debugging
- **pytest** for testing
- **black** for code formatting
- **pylint** for code linting
- **debugpy** for remote debugging
- **Git** and **GitHub CLI** for version control

# Working with the DevContainer

## Django Management Commands
All Django management commands work as expected inside the devcontainer terminal:

```bash
# Create superuser
python manage.py createsuperuser

# Run migrations
python manage.py migrate

# Start shell
python manage.py shell

# Collect static files
python manage.py collectstatic
```

## Database Access
The PostgreSQL database is automatically configured and accessible:

```bash
# Connect to database
psql -h localhost -p 5433 -U default_user -d buffalogs
```

Default credentials:
- **Username**: default_user
- **Password**: password
- **Database**: buffalogs


# Debugging
The DevContainer is configured for remote debugging:

## Django Debugging

Configure `launch.json` in VS Code for debugging.
```
{
   "name": "Python: Django Debug Service",
   "type": "debugpy",
   "request": "attach",
   "connect": {
         "host": "localhost",
         "port": 5678
   },
   "pathMappings": [
         {
            "localRoot": "${workspaceFolder}",
            "remoteRoot": "/opt/certego/buffalogs"
         }
   ],
   "justMyCode": false,
   "django": true,
   "presentation": {
         "hidden": false,
         "group": "Docker Debug"
   }
}
```

1. Set breakpoints in your code
2. Go to Run and Debug panel in VS Code
3. Select "Python: Django" configuration
4. Start debugging

## Celery Worker Debugging
The Celery worker is configured for debugging on port 5679:
1. Set breakpoints in Celery tasks
2. Create a debug configuration for port 5679
3. Go to Run and Debug panel in VS Code
4. Select "Python: Celery Worker" configuration

Note: For these configurations to appear in the Run and Debug panel in VS Code, you will have to create a `launch.json` file in a `.vscode folder` and manually add these configurations. In case of further assistance, you may reach out.

# Development Workflow

## Making Changes
1. Edit files in the `buffalogs/` directory
2. Django development server auto-reloads on changes

## Environment Variables
Key environment variables for development:
- `DEBUG=1` - Enables Django debug mode
- `CERTEGO_BUFFALOGS_DEBUG=True` - BuffaLogs-specific debug settings
- `USE_DEBUGPY=1` - Enables debugpy for remote debugging

For closing the devcontainers, go to the bottom left of your screen (in VS Code) and click on `Reopen folder locally`. This will stop all running buffalogs containers.

This DevContainer setup provides a consistent, reproducible development environment that matches the production infrastructure while offering enhanced debugging and development capabilities.