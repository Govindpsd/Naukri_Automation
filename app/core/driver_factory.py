from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import SessionNotCreatedException
from config.settings import Settings
from core.logger import logger
import time
import requests


class DriverFactory:
    @staticmethod
    def create_driver():
        selenium_url = "http://selenium:4444/wd/hub"

        # ✅ WAIT FOR SELENIUM TO BE READY
        logger.info("Waiting for Selenium Grid to be ready...")
        start = time.time()
        while time.time() - start < 60:
            try:
                response = requests.get("http://selenium:4444/wd/hub/status", timeout=5)
                if response.status_code == 200:
                    status = response.json()
                    if status.get("value", {}).get("ready", False):
                        logger.info("✓ Selenium Grid is ready")
                        # Give Selenium a moment to fully initialize
                        time.sleep(2)
                        break
            except Exception as e:
                logger.debug(f"Selenium not ready yet: {e}")
            time.sleep(2)
        else:
            raise RuntimeError("❌ Selenium did not become ready in time")

        options = Options()

        # Essential flags for containerized environments (minimal set)
        # Using minimal flags to avoid compatibility issues with Selenium Grid
        # Memory-efficient settings to prevent OOM (exit code 137)
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        # Reduced window size to save memory
        options.add_argument("--window-size=1280,720")
        # Memory-saving flags
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")

        # Try to create driver with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to create WebDriver session (attempt {attempt + 1}/{max_retries})...")
                driver = webdriver.Remote(
                    command_executor=selenium_url,
                    options=options
                )
                logger.info("✓ WebDriver session created successfully")
                driver.implicitly_wait(Settings.WAIT_TIME)
                driver.set_page_load_timeout(60)
                return driver
            except SessionNotCreatedException as e:
                error_msg = str(e)
                logger.warning(f"Session creation failed (attempt {attempt + 1}/{max_retries})")
                logger.warning(f"Error details: {error_msg}")
                
                # Try to get more details from the exception
                if hasattr(e, 'msg'):
                    logger.warning(f"Exception message: {e.msg}")
                if hasattr(e, 'stacktrace'):
                    logger.debug(f"Stacktrace: {e.stacktrace}")
                
                if attempt < max_retries - 1:
                    logger.info("Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    logger.error("Failed to create WebDriver session after all retries")
                    # Log Selenium Grid status for debugging
                    try:
                        status_response = requests.get("http://selenium:4444/wd/hub/status", timeout=5)
                        logger.info(f"Selenium Grid status: {status_response.json()}")
                    except Exception as status_error:
                        logger.warning(f"Could not get Selenium status: {status_error}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error creating driver: {e}")
                raise
