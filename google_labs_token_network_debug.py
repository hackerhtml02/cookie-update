# google_labs_token_network_debug.py
import os
import time
import json
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ----------------------------------------
# Hardcoded email (edit this if needed)
# ----------------------------------------
HARDCODE_EMAIL = "muhammadharis8765@imagescraftai.live"
# ----------------------------------------

def get_password():
    """Fetch password from environment variable."""
    pwd = os.getenv("PASSWORD") or os.getenv("GOOGLE_PASSWORD")
    if not pwd:
        print("❌ ERROR: PASSWORD not found in environment variables.")
        sys.exit(1)
    return pwd


class GoogleLabsTokenExtractor:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.setup_driver()

    def setup_driver(self):
        """Initialize headless Chrome WebDriver."""
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--incognito")
        options.add_argument("--headless=new")  # ✅ Headless by default
        options.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 30)
        print("✅ Headless Chrome WebDriver started.")

    def save_cookies(self):
        """Save or update cookies.json in repo root."""
        try:
            output_path = os.path.join(os.getcwd(), "cookies.json")
            cookies = self.driver.get_cookies()
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            print(f"💾 cookies.json saved/updated at: {output_path}")
        except Exception as e:
            print("⚠️ Could not save cookies:", e)

    def signin(self):
        """Sign in to Google Labs using hardcoded email & secret password."""
        self.driver.get("https://labs.google/fx/tools/flow")
        time.sleep(3)

        # If already signed in
        if "sign in" not in self.driver.page_source.lower():
            print("✅ Already logged in or no sign-in required.")
            self.save_cookies()
            return True

        # Enter email by ID
        try:
            email_input = self.wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
            email_input.clear()
            email_input.send_keys(self.email)
            email_input.send_keys(Keys.ENTER)
            print("📧 Email entered (ID: identifierId)")
            time.sleep(2)
        except Exception as e:
            print("❌ Email input not found by ID:", e)
            return False

        # Enter password by NAME
        try:
            password_input = self.wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
            password_input.clear()
            password_input.send_keys(self.password)
            password_input.send_keys(Keys.ENTER)
            print("🔒 Password entered (NAME: Passwd)")
            time.sleep(3)
            self.save_cookies()
            return True
        except Exception as e:
            print("❌ Password input not found by NAME:", e)
            return False

    def run(self):
        """Run login flow and save cookies."""
        try:
            self.signin()
            time.sleep(2)
        finally:
            try:
                self.driver.quit()
                print("🧹 Browser closed.")
            except:
                pass


if __name__ == "__main__":
    PASSWORD = get_password()
    EMAIL = HARDCODE_EMAIL
    print(f"Using email: {EMAIL}")
    extractor = GoogleLabsTokenExtractor(EMAIL, PASSWORD)
    extractor.run()
