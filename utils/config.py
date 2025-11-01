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

# Export Configuration
# Maximum rows per export to prevent memory issues
MAX_EXPORT_ROWS = int(os.getenv("MAX_EXPORT_ROWS", 1000000))

# Batch size for processing large datasets
EXPORT_BATCH_SIZE = int(os.getenv("EXPORT_BATCH_SIZE", 10000))

# Maximum filename length for exports
MAX_FILENAME_LENGTH = 200

# Streaming threshold - exports larger than this will use streaming (bytes)
STREAMING_THRESHOLD = 5 * 1024 * 1024  # 5MB

# Ensure required directories exist
os.makedirs(DATA_DIR, exist_ok=True)  # Ensure the data directory exists
os.makedirs(LOGS_DIR, exist_ok=True)  # Ensure the logs directory exists
