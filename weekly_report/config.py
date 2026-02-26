import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DB_PATH = os.path.join(DATA_DIR, "experiments.db")

LLM_API_KEY = os.environ.get("LLM_API_KEY", "your-api-key-here")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.example.com")
LLM_MODEL = os.environ.get("LLM_MODEL", "your-model-name")
