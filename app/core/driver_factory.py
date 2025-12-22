from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from config.settings import Settings

class DriverFactory:

    @staticmethod
    def create_driver():
        options = Options()
        if Settings.HEADLESS:
            options.add_argument("--headless=new")
            # Try to make headless less detectable
            options.add_argument("--disable-blink-features=AutomationControlled")
            # Use a common desktop user-agent to avoid simple bot detection
            options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options=options)
        try:
            # Remove webdriver flag in navigator where possible
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
        except Exception:
            pass
        driver.implicitly_wait(Settings.WAIT_TIME)
        return driver
