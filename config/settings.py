import os
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (parent of config folder)
PROJECT_ROOT = Path(__file__).parent.parent

# Load .env file from project root
env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_path)


def get_required_env(key: str) -> str:
    """Get required environment variable or raise error."""
    value = os.getenv(key)
    if not value:
        raise ValueError(
            f"❌ Missing required environment variable: {key}\n"
            f"   Please create a .env file in the project root and set {key}.\n"
            f"   See .env.example for reference."
        )
    return value


def get_optional_env(key: str, default: str) -> str:
    """Get optional environment variable with default value."""
    return os.getenv(key, default)


def get_bool_env(key: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def get_int_env(key: str, default: int) -> int:
    """Get integer environment variable."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


class Settings:
    """Application settings loaded from environment variables."""
    
    # Required credentials
    NAUKRI_EMAIL: str = get_required_env("NAUKRI_EMAIL")
    NAUKRI_PASSWORD: str = get_required_env("NAUKRI_PASSWORD")
    
    # Required URLs
    NAUKRI_PROFILE_URL: str = get_required_env("NAUKRI_PROFILE_URL")
    GITHUB_RESUME_URL: str = get_required_env("GITHUB_RESUME_URL")
    
    # Application settings
    BASE_URL: str = "https://www.naukri.com"
    LOGIN_URL: str = "https://www.naukri.com/nlogin/login"
    RESUME_TEMP_PATH: str = "Govind_Parshad_Resume.pdf"
    WAIT_TIME: int = get_int_env("WAIT_TIME", 15)
    HEADLESS: bool = get_bool_env("HEADLESS", False)

