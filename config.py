import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# 🗄️ База данных и Очередь задач
# ==============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/competitors_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ==============================================================================
# 🤖 Настройки AI
# ==============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# ==============================================================================
# 🔒 Безопасность и Frontend
# ==============================================================================
API_KEY = os.getenv("API_KEY", "sk-test-123")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# ==============================================================================
# 📁 Пути
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
FONTS_DIR = BASE_DIR / "fonts"