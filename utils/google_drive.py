import requests
from config.settings import Settings
from core.logger import logger

def download_resume():
    """
    Downloads resume from a Google Drive *public* link.
    Saves it locally as defined in Settings.RESUME_TEMP_PATH.
    """

    url = Settings.GDRIVE_RESUME_URL
    output_path = Settings.RESUME_TEMP_PATH

    try:
        logger.info(f"Downloading resume from: {url}")

        response = requests.get(url)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info("Resume downloaded successfully: " + output_path)
        return output_path

    except Exception as e:
        logger.error(f"Failed to download resume from Google Drive: {e}")
        raise
