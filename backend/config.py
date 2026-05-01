import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class Config:
    # MongoDB
    MONGO_URI               = os.getenv("MONGO_URI", "mongodb://localhost:27017/resume_checker")

    # Groq AI
    GROQ_API_KEY            = os.getenv("GROQ_API_KEY", "")

    # JWT
    JWT_SECRET_KEY          = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(minutes=int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", 15)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_REFRESH_TOKEN_DAYS", 7)))
    JWT_TOKEN_LOCATION        = ["cookies"]           # HttpOnly cookies (XSS safe)
    JWT_COOKIE_SECURE         = False                 # Set True in production (HTTPS)
    JWT_COOKIE_CSRF_PROTECT   = True                  # CSRF protection
    JWT_COOKIE_SAMESITE       = "Lax"

    # Field encryption (Fernet key — generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    ENCRYPTION_KEY          = os.getenv("ENCRYPTION_KEY", "")

    # Server
    PORT                    = int(os.getenv("PORT", 5000))
    DEBUG                   = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    # Adzuna Jobs API
    ADZUNA_APP_ID           = os.getenv("ADZUNA_APP_ID", "")
    ADZUNA_APP_KEY          = os.getenv("ADZUNA_APP_KEY", "")

    # File upload
    MAX_UPLOAD_MB           = 10
    ALLOWED_EXTENSIONS      = {"pdf", "docx", "doc", "txt"}
