from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from config.settings import Settings
import time
import requests


class DriverFactory:
    @staticmethod
    def create_driver():
        selenium_url = "http://selenium:4444/wd/hub"

        # ✅ WAIT FOR SELENIUM
        start = time.time()
        while time.time() - start < 30:
            try:
                requests.get("http://selenium:4444/status", timeout=2)
                break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError("❌ Selenium did not start in time")

        options = Options()

        if Settings.HEADLESS:
            options.add_argument("--headless=new")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument(
                "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        driver = webdriver.Remote(
            command_executor=selenium_url,
            options=options
        )

        driver.implicitly_wait(Settings.WAIT_TIME)
        return driver
