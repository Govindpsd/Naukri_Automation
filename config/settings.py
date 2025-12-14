import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    NAUKRI_EMAIL = os.getenv("NAUKRI_EMAIL")
    NAUKRI_PASSWORD = os.getenv("NAUKRI_PASSWORD")

    # Direct link to your Naukri profile edit page
    NAUKRI_PROFILE_URL = os.getenv("NAUKRI_PROFILE_URL")

    # Public Google Drive download link
    GDRIVE_RESUME_URL = os.getenv("GDRIVE_RESUME_URL")

    # Temporary downloaded resume file
    RESUME_TEMP_PATH = "resume_latest.pdf"

    BASE_URL = "https://www.naukri.com"
    WAIT_TIME = 15
    #HEADLESS = os.getenv("HEADLESS", "True") == "True"
    HEADLESS=False

