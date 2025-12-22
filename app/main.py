from core.driver_factory import DriverFactory
from workflows.update_resume_flow import UpdateResumeFlow
from core.logger import logger

def main():
    driver = DriverFactory.create_driver()
    try:
        UpdateResumeFlow().run(driver)
    except Exception as e:
        logger.error(f"Automation failed: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
