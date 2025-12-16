import json
import os
from pathlib import Path
from selenium.webdriver.remote.webdriver import WebDriver
from core.logger import logger

# Cookie file path
COOKIE_FILE = Path(__file__).parent.parent / "cookies.json"


def save_cookies(driver: WebDriver):
    """Save browser cookies to a JSON file."""
    try:
        cookies = driver.get_cookies()
        with open(COOKIE_FILE, 'w') as f:
            json.dump(cookies, f, indent=2)
        logger.info(f"✓ Saved {len(cookies)} cookies to {COOKIE_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save cookies: {e}")
        return False


def load_cookies(driver: WebDriver) -> bool:
    """Load cookies from JSON file and add them to the browser."""
    if not COOKIE_FILE.exists():
        logger.info("No saved cookies found")
        return False
    
    try:
        with open(COOKIE_FILE, 'r') as f:
            cookies = json.load(f)
        
        # Navigate to the domain first (required for adding cookies)
        driver.get("https://www.naukri.com")
        
        for cookie in cookies:
            try:
                # Remove 'expiry' if it's in the past or if it's not a valid format
                if 'expiry' in cookie:
                    # Check if cookie is expired (optional - you can remove this check)
                    pass
                driver.add_cookie(cookie)
            except Exception as e:
                logger.warning(f"Could not add cookie {cookie.get('name', 'unknown')}: {e}")
                continue
        
        logger.info(f"✓ Loaded {len(cookies)} cookies from {COOKIE_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to load cookies: {e}")
        return False


def clear_cookies():
    """Delete the saved cookies file."""
    try:
        if COOKIE_FILE.exists():
            COOKIE_FILE.unlink()
            logger.info("✓ Cleared saved cookies")
            return True
    except Exception as e:
        logger.error(f"Failed to clear cookies: {e}")
        return False


def is_logged_in(driver: WebDriver) -> bool:
    """Check if user is logged in by checking for logged-in indicators."""
    try:
        # Refresh the page to ensure we're using the loaded cookies
        driver.get("https://www.naukri.com")
        
        # Wait a bit for page to load
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check for indicators that user is logged in
        # Common indicators: profile link, logout button, user menu, etc.
        logged_in_indicators = [
            "//a[contains(@href, '/mnjuser/profile')]",
            "//a[contains(@title, 'My Naukri')]",
            "//div[contains(@class, 'user-name')]",
            "//a[contains(text(), 'Logout')]",
            "//div[contains(@class, 'logged-in')]",
        ]
        
        from selenium.common.exceptions import TimeoutException
        for indicator in logged_in_indicators:
            try:
                element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, indicator))
                )
                if element:
                    logger.info("✓ User appears to be logged in (found logged-in indicator)")
                    return True
            except TimeoutException:
                continue
        
        # Alternative: Check if we're redirected away from login page
        current_url = driver.current_url.lower()
        if "login" not in current_url and "naukri.com" in current_url:
            logger.info("✓ User appears to be logged in (not on login page)")
            return True
        
        logger.info("✗ User does not appear to be logged in")
        return False
    except Exception as e:
        logger.warning(f"Could not verify login status: {e}")
        return False

