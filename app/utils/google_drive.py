import requests
from config.settings import Settings
from core.logger import logger

def download_resume():
    """
    Downloads resume from GitHub using a raw file URL.
    Saves it locally as defined in Settings.RESUME_TEMP_PATH.
    
    GitHub URL format: https://raw.githubusercontent.com/username/repo/branch/path/to/resume.pdf
    """

    url = Settings.GITHUB_RESUME_URL
    output_path = Settings.RESUME_TEMP_PATH

    try:
        logger.info(f"Downloading resume from GitHub: {url}")

        # GitHub raw URLs work well with a simple GET request
        # Add headers to ensure proper content type handling
        headers = {
            'Accept': 'application/octet-stream',
            'User-Agent': 'Mozilla/5.0'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info("Resume downloaded successfully: " + output_path)
        return output_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download resume from GitHub: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while downloading resume: {e}")
        raise
