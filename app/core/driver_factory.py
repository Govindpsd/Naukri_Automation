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
                        # Give Selenium more time to fully initialize and free up memory
                        logger.info("Waiting 5 seconds for Selenium to stabilize...")
                        time.sleep(5)
                        break
            except Exception as e:
                logger.debug(f"Selenium not ready yet: {e}")
            time.sleep(2)
        else:
            raise RuntimeError("❌ Selenium did not become ready in time")

        options = Options()

        # Essential flags for containerized environments (minimal set)
        # Using minimal flags to avoid compatibility issues with Selenium Grid
        # Aggressive memory-efficient settings to prevent OOM (exit code 137)
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        # Minimal window size to save memory
        options.add_argument("--window-size=1024,768")
        # Aggressive memory-saving flags
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees,VizDisplayCompositor")
        # Additional memory optimizations
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-hang-monitor")
        options.add_argument("--disable-prompt-on-repost")
        options.add_argument("--disable-domain-reliability")
        options.add_argument("--disable-component-update")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-breakpad")
        options.add_argument("--disable-client-side-phishing-detection")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-prompt-on-repost")
        options.add_argument("--disable-translate")
        options.add_argument("--metrics-recording-only")
        options.add_argument("--mute-audio")
        # Limit renderer process count
        options.add_argument("--renderer-process-limit=1")
        # Disable image loading to save memory
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Block images
            "profile.default_content_setting_values": {
                "notifications": 2,
                "geolocation": 2,
            }
        }
        options.add_experimental_option("prefs", prefs)

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
