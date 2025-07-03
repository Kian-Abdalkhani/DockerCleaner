import subprocess
import schedule
import logging
import logging.handlers
import os
import json

# Configuration: Stack names to exclude from restart
# This prevents the script from restarting itself when running in Docker
EXCLUDED_STACKS = [
    "homeserver-scripts",  # Default name from docker-compose.yml
    os.getenv("COMPOSE_PROJECT_NAME", ""),  # Environment variable override
]

def setup_logging():
    # Create a logs/ directory if it doesn't exist
    os.makedirs(r'../logs', exist_ok=True)

    # Use a single log filename without a timestamp
    log_filename = r'../logs/app.log'

    # Configure logging with rotating file handler
    # maxBytes: 1MB file size limit
    # backupCount: Keep 2 backup files (app.log.1, app.log.2)
    rotating_handler = logging.handlers.RotatingFileHandler(
        log_filename, 
        maxBytes=1024*1024,  # 1MB
        backupCount=0
    )

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            rotating_handler,
            logging.StreamHandler()  # Also output to console
        ]
    )

    # Get logger and log setup completion
    return logging.getLogger(__name__)

def get_running_compose_stacks():
    """Get all running Docker Compose stacks"""
    # Get a list of running compose stacks
    result = subprocess.run(
        ["docker", "compose", "ls", "--format", "json"],
        capture_output=True,
        text=True,
        check=True
    )

    # Parse JSON output
    stacks = json.loads(result.stdout)

    # Filter only running stacks
    running_stacks = [stack for stack in stacks if stack.get('Status', '').startswith('running')]

    return running_stacks

def restart_compose_stack(stack_name, config_files):
    """Restart a specific Docker Compose stack"""
    # Build the compose command with config files
    compose_cmd = ["docker", "compose"]

    # Add config files
    for config_file in config_files.split(','):
        compose_cmd.extend(["-f", config_file.strip()])

    # Add the project name
    compose_cmd.extend(["-p", stack_name])

    # Stop the stack
    logging.info(f"Stopping stack: {stack_name}")
    subprocess.run(compose_cmd + ["down"], check=True)

    # Start the stack
    logging.info(f"Starting stack: {stack_name}")
    subprocess.run(compose_cmd + ["up", "-d"], check=True)

    logging.info(f"Successfully restarted stack: {stack_name}")
    return True

def restart_all_running_stacks():
    """Restart all currently running Docker Compose stacks (excluding self)"""
    running_stacks = get_running_compose_stacks()

    if not running_stacks:
        logging.info("No running Docker Compose stacks found")
        return

    # Filter out excluded stacks (including this script's own stack)
    filtered_stacks = []
    excluded_count = 0

    for stack in running_stacks:
        stack_name = stack.get('Name', '')
        # Check if this stack should be excluded
        if stack_name in EXCLUDED_STACKS or stack_name == "":
            logging.info(f"Excluding stack from restart: {stack_name}")
            excluded_count += 1
        else:
            filtered_stacks.append(stack)

    logging.info(f"Found {len(running_stacks)} running stacks, excluding {excluded_count} stacks")

    if not filtered_stacks:
        logging.info("No stacks to restart after applying exclusions")
        return

    successful_restarts = 0
    for stack in filtered_stacks:
        stack_name = stack.get('Name', '')
        config_files = stack.get('ConfigFiles', '')

        logging.info(f"Restarting stack: {stack_name}")

        if restart_compose_stack(stack_name, config_files):
            successful_restarts += 1

    logging.info(f"Successfully restarted {successful_restarts}/{len(filtered_stacks)} stacks")

def docker_cleanup():
    logger.info("Running docker cleanup")
    subprocess.run(["docker","system","prune","-f"])
    logger.info("Docker cleanup complete")

schedule.every().monday.at("03:00").do(docker_cleanup)
schedule.every().monday.at("04:00").do(restart_all_running_stacks)

if __name__ == "__main__":
    logger = setup_logging()
    logger.info(f"Logging initialized. Starting scheduler...")
    while True:
        schedule.run_pending()
