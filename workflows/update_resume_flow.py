from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from config.settings import Settings
from utils.google_drive import download_resume
from core.logger import logger

import os


# ------------------------------------------------------------
# SMART WAIT HELPERS
# ------------------------------------------------------------

def wait_for(driver, by, value, timeout=12):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )

def wait_clickable(driver, by, value, timeout=12):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )


# ------------------------------------------------------------
# CLOSE CHATBOT IF VISIBLE
# ------------------------------------------------------------

def close_chatbot_if_visible(driver):

    possible_close_buttons = [
        "//button[contains(@class, 'close')]",
        "//div[contains(@class, 'close')]",
        "//span[contains(text(), '×')]",
        "//button//*[local-name()='svg']",
        "//*[@id='chatbot-close']",
        "//img[contains(@src, 'close')]",
        "//div[@role='dialog']//button",
        "//button[@aria-label='Close']",
    ]

    for xpath in possible_close_buttons:
        try:
            elem = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            elem.click()
            logger.info("Chatbot closed.")
            return True
        except:
            continue

    return False


# ------------------------------------------------------------
# CLICK LOGIN BUTTON
# ------------------------------------------------------------

def click_login_button(driver):

    login_locators = [
        (By.ID, "login_Layer"),
        (By.XPATH, "//a[@title='Jobseeker Login']"),
        (By.XPATH, "//a[contains(@class, 'nI-gNb-lg-rg__login')]"),
        (By.XPATH, "//a[contains(text(), 'Login')]"),
    ]

    for by, locator in login_locators:
        try:
            btn = wait_clickable(driver, by, locator, timeout=8)
            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            btn.click()
            logger.info("Clicked Login button.")
            return True
        except TimeoutException:
            continue

    raise Exception("❌ Login button not found — Naukri UI changed.")



# ------------------------------------------------------------
# MAIN WORKFLOW
# ------------------------------------------------------------

class UpdateResumeFlow:

    def run(self, driver):

        logger.info("🚀 Starting Naukri resume update automation")

        # ------------------------------------------------------------
        # 1. DOWNLOAD RESUME FROM GOOGLE DRIVE
        # ------------------------------------------------------------
        resume_path = download_resume()

        # Convert to ABSOLUTE path (critical)
        resume_path = os.path.abspath(resume_path)
        logger.info(f"Using resume file: {resume_path}")


        # ------------------------------------------------------------
        # 2. LOGIN
        # ------------------------------------------------------------

        driver.get(Settings.BASE_URL)
        close_chatbot_if_visible(driver)

        click_login_button(driver)
        close_chatbot_if_visible(driver)

        # Email input
        email_input = wait_for(
            driver,
            By.XPATH,
            "//input[@type='text' and contains(@placeholder, 'Email')]"
        )
        email_input.send_keys(Settings.NAUKRI_EMAIL)

        # Password input
        password_input = wait_for(
            driver,
            By.XPATH,
            "//input[@type='password' and contains(@placeholder, 'password')]"
        )
        password_input.send_keys(Settings.NAUKRI_PASSWORD)

        # Login submit
        login_submit = wait_clickable(
            driver,
            By.XPATH,
            "//button[contains(text(),'Login')]"
        )
        login_submit.click()

        logger.info("🔐 Logged into Naukri.")
        close_chatbot_if_visible(driver)


        # ------------------------------------------------------------
        # 3. NAVIGATE TO PROFILE PAGE
        # ------------------------------------------------------------
        driver.get(Settings.NAUKRI_PROFILE_URL)

        wait_for(driver, By.TAG_NAME, "body", timeout=10)
        close_chatbot_if_visible(driver)


        # ------------------------------------------------------------
        # 4. UPLOAD RESUME — via REAL hidden input attachCV
        # ------------------------------------------------------------

        try:
            logger.info("Looking for hidden upload input 'attachCV'...")

            # 1. Locate the hidden <input type="file" id="attachCV">
            upload_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "attachCV"))
            )

            logger.info("Found attachCV input field.")

            # 2. Make hidden input visible so Selenium can interact
            driver.execute_script("arguments[0].style.display = 'block';", upload_input)

            # 3. Upload file using absolute path
            logger.info(f"Uploading resume from: {resume_path}")
            upload_input.send_keys(resume_path)

            logger.info("✅ Resume uploaded successfully!")

        except Exception as e:
            logger.error(f"❌ Could not upload resume: {e}")
            raise


        logger.info("🎉 Naukri resume automation completed successfully.")
