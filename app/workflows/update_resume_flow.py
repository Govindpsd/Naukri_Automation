from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

from config.settings import Settings
from utils.google_drive import download_resume
from utils.session_manager import load_cookies, save_cookies, is_logged_in
from core.logger import logger

import os
import time


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


# Search for file input across main document and inside iframes
def find_file_input(driver, locators, per_locator_timeout=5):
    # Try the provided locators in the main document first
    for by, locator in locators:
        try:
            logger.info(f"Trying file input locator: {locator}")
            elem = WebDriverWait(driver, per_locator_timeout).until(
                EC.presence_of_element_located((by, locator))
            )
            if elem:
                return elem, None
        except TimeoutException:
            continue

    # Try a generic querySelector in main document
    try:
        elem = driver.execute_script("return document.querySelector('input[type=file]');")
        if elem:
            logger.info("✓ Found file input via querySelector in main document")
            return elem, None
    except Exception:
        pass

    # Search inside iframes
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    for idx, iframe in enumerate(iframes):
        try:
            logger.info(f"Searching for file input inside iframe[{idx}]")
            driver.switch_to.frame(iframe)

            for by, locator in locators:
                try:
                    logger.info(f"Trying file input locator in iframe[{idx}]: {locator}")
                    elem = WebDriverWait(driver, per_locator_timeout).until(
                        EC.presence_of_element_located((by, locator))
                    )
                    if elem:
                        return elem, iframe
                except TimeoutException:
                    continue

            try:
                elem = driver.execute_script("return document.querySelector('input[type=file]');")
                if elem:
                    logger.info(f"✓ Found file input via querySelector in iframe[{idx}]")
                    return elem, iframe
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"Could not inspect iframe[{idx}]: {e}")
        finally:
            driver.switch_to.default_content()

    return None, None


# Fallback: deep JS search to find input[type=file] across document, shadow roots and iframes
def find_file_input_js(driver):
    js = r"""
    function findInNode(node){
        if(!node) return null;
        try{
            // Direct match
            var inputs = node.querySelectorAll('input[type=file]');
            if(inputs && inputs.length) return inputs[0];
        }catch(e){}

        // shadow root search
        try{
            if(node.shadowRoot){
                var s = node.shadowRoot.querySelectorAll('input[type=file]');
                if(s && s.length) return s[0];
            }
        }catch(e){}

        // traverse children
        try{
            var children = node.children || [];
            for(var i=0;i<children.length;i++){
                var found = findInNode(children[i]);
                if(found) return found;
            }
        }catch(e){}

        return null;
    }

    // Try main document
    var found = findInNode(document);
    if(found) return found;

    // Try iframes (same-origin only)
    var iframes = document.getElementsByTagName('iframe');
    for(var i=0;i<iframes.length;i++){
        try{
            var doc = iframes[i].contentDocument || iframes[i].contentWindow.document;
            var f = findInNode(doc);
            if(f) return f;
        }catch(e){
            // cross-origin or access denied
            continue;
        }
    }

    return null;
    """

    try:
        elem = driver.execute_script(js)
        return elem
    except Exception:
        return None

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
# PERFORM LOGIN
# ------------------------------------------------------------

def perform_login(driver):
    """Perform login with email and password."""
    # Navigate directly to login page
    logger.info(f"Navigating to login page: {Settings.LOGIN_URL}")
    driver.get(Settings.LOGIN_URL)
    
    # Wait for page to load
    wait_for(driver, By.TAG_NAME, "body", timeout=15)
    close_chatbot_if_visible(driver)

    # Try multiple selectors for email input
    email_locators = [
        (By.XPATH, "//input[@type='text' and contains(@placeholder, 'Email')]"),
        (By.XPATH, "//input[@type='text' and contains(@placeholder, 'email')]"),
        (By.XPATH, "//input[@type='email']"),
        (By.XPATH, "//input[@name='email']"),
        (By.XPATH, "//input[@id='usernameField']"),
        (By.XPATH, "//input[contains(@class, 'email') or contains(@class, 'username')]"),
    ]
    
    email_input = None
    for by, locator in email_locators:
        try:
            logger.info(f"Trying email locator: {locator}")
            email_input = wait_for(driver, by, locator, timeout=5)
            if email_input:
                logger.info(f"✓ Found email input with: {locator}")
                break
        except TimeoutException:
            continue
    
    if not email_input:
        raise Exception("❌ Could not find email input field on login page")
    
    email_input.clear()
    email_input.send_keys(Settings.NAUKRI_EMAIL)
    logger.info("✓ Email entered")

    # Try multiple selectors for password input
    password_locators = [
        (By.XPATH, "//input[@type='password' and contains(@placeholder, 'password')]"),
        (By.XPATH, "//input[@type='password' and contains(@placeholder, 'Password')]"),
        (By.XPATH, "//input[@type='password']"),
        (By.XPATH, "//input[@name='password']"),
        (By.XPATH, "//input[@id='passwordField']"),
    ]
    
    password_input = None
    for by, locator in password_locators:
        try:
            logger.info(f"Trying password locator: {locator}")
            password_input = wait_for(driver, by, locator, timeout=5)
            if password_input:
                logger.info(f"✓ Found password input with: {locator}")
                break
        except TimeoutException:
            continue
    
    if not password_input:
        raise Exception("❌ Could not find password input field on login page")
    
    password_input.clear()
    password_input.send_keys(Settings.NAUKRI_PASSWORD)
    logger.info("✓ Password entered")

    # Try multiple selectors for login button
    login_button_locators = [
        (By.XPATH, "//button[contains(text(),'Login')]"),
        (By.XPATH, "//button[@type='submit']"),
        (By.XPATH, "//input[@type='submit']"),
        (By.XPATH, "//button[contains(@class, 'login')]"),
        (By.XPATH, "//button[contains(@class, 'submit')]"),
    ]
    
    login_submit = None
    for by, locator in login_button_locators:
        try:
            logger.info(f"Trying login button locator: {locator}")
            login_submit = wait_clickable(driver, by, locator, timeout=5)
            if login_submit:
                logger.info(f"✓ Found login button with: {locator}")
                break
        except TimeoutException:
            continue
    
    if not login_submit:
        raise Exception("❌ Could not find login button on login page")
    
    login_submit.click()
    logger.info("✓ Login button clicked")

    # Wait for login to complete (check if we're redirected away from login page)
    try:
        WebDriverWait(driver, 15).until(
            lambda d: "login" not in d.current_url.lower() or d.current_url == Settings.NAUKRI_PROFILE_URL
        )
    except TimeoutException:
        logger.warning("Still on login page after clicking login - might need manual verification")

    logger.info("🔐 Logged into Naukri.")
    close_chatbot_if_visible(driver)
    
    # Save cookies after successful login
    save_cookies(driver)


# ------------------------------------------------------------
# MAIN WORKFLOW
# ------------------------------------------------------------

class UpdateResumeFlow:

    def run(self, driver):

        logger.info("🚀 Starting Naukri resume update automation")

        # ------------------------------------------------------------
        # 1. DOWNLOAD RESUME FROM GITHUB
        # ------------------------------------------------------------
        resume_path = download_resume()

        # Convert to ABSOLUTE path (critical)
        resume_path = os.path.abspath(resume_path)
        logger.info(f"Using resume file: {resume_path}")


        # ------------------------------------------------------------
        # 2. LOGIN (with cookie-based session management)
        # ------------------------------------------------------------

        # Try to load saved cookies first
        logger.info("Attempting to load saved session cookies...")
        cookies_loaded = load_cookies(driver)
        
        if cookies_loaded:
            # Check if we're already logged in with the cookies
            if is_logged_in(driver):
                logger.info("✅ Successfully logged in using saved cookies (bypassed login form)")
                close_chatbot_if_visible(driver)
            else:
                logger.info("Cookies loaded but session expired. Performing fresh login...")
                perform_login(driver)
        else:
            logger.info("No saved cookies found. Performing fresh login...")
            perform_login(driver)


        # ------------------------------------------------------------
        # 3. NAVIGATE TO PROFILE PAGE
        # ------------------------------------------------------------
        logger.info(f"Navigating to profile page: {Settings.NAUKRI_PROFILE_URL}")
        driver.get(Settings.NAUKRI_PROFILE_URL)

        # Wait for page to fully load
        wait_for(driver, By.TAG_NAME, "body", timeout=15)
        close_chatbot_if_visible(driver)
        
        # Wait a bit more for dynamic content to load
        time.sleep(3)
        
        # Scroll to resume section to ensure it's in view
        try:
            resume_section = driver.find_element(By.XPATH, "//*[contains(text(), 'Resume') or contains(@id, 'resume') or contains(@class, 'resume')]")
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", resume_section)
            logger.info("✓ Scrolled to resume section")
            time.sleep(2)
        except:
            logger.warning("Could not find resume section to scroll to - continuing anyway")


        # ------------------------------------------------------------
        # 4. UPLOAD RESUME
        # ------------------------------------------------------------

        try:
            logger.info("Looking for resume upload input field...")
            
            # Wait for the resume section to be visible
            wait_for(driver, By.TAG_NAME, "body", timeout=10)
            
            # Try multiple strategies to find and interact with the file input
            upload_input = None
            iframe_ctx = None

            # Strategy 1: Look for attachCV by ID (most common)
            file_input_locators = [
                (By.ID, "attachCV"),
                (By.NAME, "attachCV"),
                (By.XPATH, "//input[@type='file' and @id='attachCV']"),
                (By.XPATH, "//input[@type='file' and @name='attachCV']"),
                (By.XPATH, "//input[@type='file' and contains(@class, 'attachCV')]") ,
                (By.XPATH, "//input[@type='file']"),
            ]

            # Use iframe-aware finder helper
            upload_input, iframe_ctx = find_file_input(driver, file_input_locators, per_locator_timeout=5)

            if not upload_input:
                # Strategy 2: Try clicking the "Update resume" button first to trigger file input
                logger.info("File input not found directly. Trying to click 'Update resume' button...")
                update_button_locators = [
                    (By.XPATH, "//input[@type='button' and @value='Update resume']"),
                    (By.XPATH, "//button[contains(text(), 'Update resume')]") ,
                    (By.XPATH, "//input[contains(@class, 'dummyUpload')]") ,
                    (By.XPATH, "//button[contains(@class, 'dummyUpload')]") ,
                    (By.XPATH, "//*[contains(text(), 'Update resume')]") ,
                ]

                update_button = None
                for by, locator in update_button_locators:
                    try:
                        update_button = wait_clickable(driver, by, locator, timeout=5)
                        if update_button:
                            logger.info(f"✓ Found update button with: {locator}")
                            # Click the button to trigger file input
                            try:
                                update_button.click()
                            except Exception:
                                driver.execute_script("arguments[0].click();", update_button)
                            logger.info("✓ Clicked update button")
                            # Wait a bit for file input to appear
                            time.sleep(2)
                            break
                    except TimeoutException:
                        continue

                # Try finding file input again after clicking the button
                upload_input, iframe_ctx = find_file_input(driver, file_input_locators, per_locator_timeout=5)

            if not upload_input:
                # Try deep JS-based search (shadow DOM / iframes)
                logger.info("Attempting deep JS search for file input (shadow DOM / iframes)...")
                try:
                    js_elem = find_file_input_js(driver)
                    if js_elem:
                        upload_input = js_elem
                        iframe_ctx = None
                        logger.info("✓ Found file input via JS fallback")
                except Exception:
                    pass

            if not upload_input:
                raise Exception("❌ Could not find file upload input field. Naukri UI may have changed.")
            
            # If the input was found inside an iframe, switch into that frame
            switched_to_frame = False
            if iframe_ctx:
                try:
                    driver.switch_to.frame(iframe_ctx)
                    switched_to_frame = True
                    logger.info("Switched into iframe context to interact with file input")
                except Exception as e:
                    logger.warning(f"Could not switch to iframe context: {e}")

            # Make sure the input is visible and interactable
            try:
                # Remove any display:none or visibility:hidden styles
                driver.execute_script("""
                    arguments[0].style.display = 'block';
                    arguments[0].style.visibility = 'visible';
                    arguments[0].style.opacity = '1';
                    arguments[0].style.position = 'static';
                    arguments[0].style.height = 'auto';
                    arguments[0].style.width = 'auto';
                """, upload_input)
            except Exception as e:
                logger.warning(f"Could not modify input styles: {e}")

            # Upload the file
            logger.info(f"Uploading resume from: {resume_path}")

            # First, ensure the file input is ready
            try:
                # Trigger focus event
                driver.execute_script("arguments[0].focus();", upload_input)
                time.sleep(0.5)
            except Exception:
                pass

            # Send the file path
            upload_input.send_keys(resume_path)
            logger.info("✓ File path sent to input field")
            
            # Trigger change event (often required for file uploads to work)
            try:
                driver.execute_script("""
                    var input = arguments[0];
                    var event = new Event('change', { bubbles: true });
                    input.dispatchEvent(event);
                """, upload_input)
                logger.info("✓ Triggered change event on file input")
            except Exception as e:
                logger.warning(f"Could not trigger change event: {e}")
            
            # Wait a moment for the file selection to register
            time.sleep(2)

            # If we had switched into an iframe to interact with the input, switch back now
            if switched_to_frame:
                try:
                    driver.switch_to.default_content()
                    logger.info("Switched back to default content after interacting with iframe")
                except Exception:
                    pass
            
            # Verify file was actually selected
            try:
                file_value = upload_input.get_attribute('value')
                if file_value:
                    logger.info(f"✓ File input value confirmed: {file_value}")
                else:
                    logger.warning("⚠ File input value is empty - file may not have been selected")
            except Exception as e:
                logger.warning(f"Could not verify file input value: {e}")
            
            # Check for upload progress indicators or submit buttons
            logger.info("Checking for upload progress or submit buttons...")
            
            # Look for submit/confirm/save buttons that might appear after file selection
            submit_button_locators = [
                (By.XPATH, "//button[contains(text(), 'Submit')]"),
                (By.XPATH, "//button[contains(text(), 'Save')]"),
                (By.XPATH, "//button[contains(text(), 'Upload')]"),
                (By.XPATH, "//button[contains(text(), 'Confirm')]"),
                (By.XPATH, "//input[@type='submit']"),
                (By.XPATH, "//button[@type='submit']"),
            ]
            
            submit_button = None
            for by, locator in submit_button_locators:
                try:
                    submit_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((by, locator))
                    )
                    if submit_button:
                        logger.info(f"✓ Found submit button: {locator}")
                        submit_button.click()
                        logger.info("✓ Clicked submit button")
                        time.sleep(2)
                        break
                except TimeoutException:
                    continue
            
            # Wait for upload to complete - look for multiple success indicators
            logger.info("Waiting for upload to complete...")
            upload_success = False
            
            # Wait up to 45 seconds for upload completion
            for attempt in range(15):  # Check every 3 seconds for 45 seconds total
                time.sleep(3)
                
                # Check 1: Look for success messages
                try:
                    success_indicators = driver.find_elements(By.XPATH, 
                        "//*[contains(text(), 'successfully') or contains(text(), 'uploaded') or contains(text(), 'updated')]"
                    )
                    if success_indicators:
                        logger.info("✓ Found success message on page")
                        upload_success = True
                        break
                except:
                    pass
                
                # Check 2: Look for error messages
                try:
                    error_indicators = driver.find_elements(By.XPATH,
                        "//*[contains(text(), 'error') or contains(text(), 'failed') or contains(text(), 'invalid')]"
                    )
                    if error_indicators:
                        error_text = error_indicators[0].text
                        logger.warning(f"⚠ Found potential error message: {error_text}")
                except:
                    pass
                
                # Check 3: Look for upload progress indicators disappearing
                try:
                    progress_bars = driver.find_elements(By.XPATH, "//*[contains(@class, 'progress') or contains(@class, 'loading')]")
                    if not progress_bars:
                        # No progress bars might mean upload is done
                        logger.info("✓ Upload progress indicators disappeared")
                    else:
                        logger.info(f"Upload in progress... (attempt {attempt + 1}/15)")
                except:
                    pass
                
                # Check 4: Verify file name appears on page (most reliable)
                file_name = os.path.basename(resume_path)
                try:
                    # Look for the file name in various places
                    file_elements = driver.find_elements(By.XPATH, 
                        f"//*[contains(text(), '{file_name}') or contains(text(), '{file_name.replace('.pdf', '')}')]"
                    )
                    if file_elements:
                        logger.info(f"✓ Verified: File name appears on page")
                        upload_success = True
                        break
                except:
                    pass
                
                # Check 5: Page URL change or reload
                current_url = driver.current_url
                if "profile" in current_url.lower():
                    logger.info("Still on profile page, upload may be processing...")
            
            if upload_success:
                logger.info("✅ Resume upload verified successfully!")
            else:
                logger.warning("⚠ Upload completion could not be verified. Please check manually.")
                # Take a screenshot for debugging
                try:
                    screenshot_path = "upload_verification_screenshot.png"
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"Screenshot saved to: {screenshot_path}")
                except:
                    pass
            
            logger.info("✅ Resume upload process completed!")

        except Exception as e:
            logger.error(f"❌ Could not upload resume: {e}")
            # Take a screenshot for debugging
            try:
                screenshot_path = "upload_error_screenshot.png"
                driver.save_screenshot(screenshot_path)
                logger.info(f"Screenshot saved to: {screenshot_path}")
            except:
                pass
            raise


        logger.info("🎉 Naukri resume automation completed successfully.")
