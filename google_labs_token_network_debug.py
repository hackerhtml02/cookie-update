# google_labs_token_network_debug.py
import os, time, json, sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ----------------------------------------
# Hardcoded Email
# ----------------------------------------
HARDCODE_EMAIL = "muhammadharis8765@imagescraftai.live"

def get_password():
    pwd = os.getenv("PASSWORD") or os.getenv("GOOGLE_PASSWORD")
    if not pwd:
        print("❌ ERROR: PASSWORD not found in environment variables.")
        sys.exit(1)
    return pwd

class GoogleLabsTokenExtractor:
    def __init__(self, email, password, headless=True):
        self.email = email
        self.password = password
        self.headless = headless
        self.setup_driver()

    def setup_driver(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--incognito")
        if self.headless:
            options.add_argument("--headless=new")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 30)
        print("✅ Chrome WebDriver started.")

    def save_cookies(self):
        try:
            output_path = os.path.join(os.getcwd(), "cookies.json")
            cookies = self.driver.get_cookies()
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            print(f"💾 cookies.json saved/updated successfully at: {output_path}")
        except Exception as e:
            print("⚠️ Could not save cookies:", e)

    def signin(self):
        self.driver.get("https://labs.google/fx/tools/flow")
        time.sleep(2)

        # If already signed in
        if "sign in" not in self.driver.page_source.lower():
            print("✅ Already logged in or no sign-in required.")
            self.save_cookies()
            return True

        try:
            email_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
            email_input.send_keys(self.email)
            email_input.send_keys(Keys.ENTER)
            print("📧 Email entered.")
            time.sleep(2)
        except Exception as e:
            print("❌ Email input not found:", e)
            return False

        try:
            password_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
            password_input.send_keys(self.password)
            password_input.send_keys(Keys.ENTER)
            print("🔒 Password submitted.")
            time.sleep(3)
            self.save_cookies()
            return True
        except Exception as e:
            print("❌ Password input not found:", e)
            return False

    def run(self):
        try:
            self.signin()
            time.sleep(2)
        finally:
            try:
                self.driver.quit()
            except:
                pass

if __name__ == "__main__":
    PASSWORD = get_password()
    print(f"Using email: {HARDCODE_EMAIL} (hardcoded)")
    extractor = GoogleLabsTokenExtractor(HARDCODE_EMAIL, PASSWORD, headless=True)
    extractor.run()
