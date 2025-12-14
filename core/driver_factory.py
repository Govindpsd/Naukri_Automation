from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from config.settings import Settings

class DriverFactory:

    @staticmethod
    def create_driver():
        options = Options()
        if Settings.HEADLESS:
            options.add_argument("--headless=new")

        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(Settings.WAIT_TIME)
        return driver
