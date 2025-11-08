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

HARDCODE_EMAIL = "muhammadharis8765@imagescraftai.live"

def get_password():
    pwd = os.getenv("PASSWORD") or os.getenv("GOOGLE_PASSWORD")
    if not pwd:
        print("❌ ERROR: PASSWORD not found in environment variables.")
        sys.exit(1)
    return pwd

class GoogleLabsToken:
    def __init__(self, email, password, headless=True):
        self.email = email
        self.password = password
        self.headless = headless
        self.setup_driver()

    def setup_driver(self):
        opts = Options()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("--incognito")
        if self.headless:
            opts.add_argument("--headless=new")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opts)
        self.wait = WebDriverWait(self.driver, 30)
        print("✅ Chrome WebDriver started.")

    def save_cookies(self):
        try:
            cookies = self.driver.get_cookies()
            with open("cookies.json", "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            print("💾 cookies.json saved in repo directory.")
        except Exception as e:
            print("⚠️ Failed to save cookies:", e)

    def signin(self):
        self.driver.get("https://labs.google/fx/tools/flow")
        time.sleep(2)
        if "sign in" not in self.driver.page_source.lower():
            print("✅ Already logged in or no sign-in required.")
            self.save_cookies()
            return True

        try:
            email_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
            email_input.send_keys(self.email)
            email_input.send_keys(Keys.ENTER)
            time.sleep(2)
            pwd_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
            pwd_input.send_keys(self.password)
            pwd_input.send_keys(Keys.ENTER)
            time.sleep(3)
            self.save_cookies()
            return True
        except Exception as e:
            print("❌ Sign-in failed:", e)
            return False

    def run(self):
        try:
            self.signin()
            time.sleep(3)
        finally:
            try:
                self.driver.quit()
            except:
                pass

if __name__ == "__main__":
    PASSWORD = get_password()
    print(f"Using email: {HARDCODE_EMAIL}")
    GoogleLabsToken(HARDCODE_EMAIL, PASSWORD, headless=True).run()
