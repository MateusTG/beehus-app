from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, date


class SeleniumHelpers:
    def __init__(self, driver, timeout=50):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
    
    # clickable element
    def click_element(self, by, value):
        element = self.wait.until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()

    # any clickable elements
    def click_any_element(self, by, values: list):
        element = self.wait.until(
            EC.any_of(
                *[EC.element_to_be_clickable((by, v)) for v in values]
            )
        )
        element.click()


    def find_element(self, by, value):
        element = self.wait.until(
            EC.presence_of_element_located((by, value))
        )
        # element.click()
        return element
    
    def find_any_element(self, by, values: list):
        element = self.wait.until(
            EC.any_of(
                *[EC.presence_of_element_located((by, v)) for v in values]
            )
        )
        # element.click()
        return element
    
    def hover_element(self, by, value):
        element = self.driver.find_element(by, value)
        ActionChains(self.driver).move_to_element(element).perform()
    
    def wait_for_element(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    