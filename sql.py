import os
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get environment variables
pg_host = os.getenv("POSTGRES_HOST")
pg_user = os.getenv("POSTGRES_USER")
pg_password = os.getenv("POSTGRES_PASSWORD")
pg_db = os.getenv("POSTGRES_NAME")
pg_port = os.getenv("POSTGRES_PORT")

# Construct the psql command
psql_command = [
    "psql",
    "-h", pg_host,
    "-U", pg_user,
    "-d", pg_db,
    "-p", pg_port
]

# Run the command
subprocess.run(psql_command, env={**os.environ, "PGPASSWORD": pg_password})
