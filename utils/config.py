import os

# Paths
# Set BASE_DIR to the root of the project
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")  # Centralized data folder
LOGS_DIR = os.path.join(BASE_DIR, "logs")  # Centralized logs folder

# Database File
DB_FILE = os.getenv("DB_FILE", os.path.join(DATA_DIR, "database.db"))  # Allow override via environment variable

# Application Constants
APP_TITLE = "Workout Tracker"

# Ensure required directories exist
os.makedirs(DATA_DIR, exist_ok=True)  # Ensure the data directory exists
os.makedirs(LOGS_DIR, exist_ok=True)  # Ensure the logs directory exists
