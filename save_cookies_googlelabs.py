# save_as: save_cookies_googlelabs.py
import os
import time
import json
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# ---- Put your email here (hard-coded as you requested) ----
EMAIL = "muhammadharis8765@imagescraftai.live"   # <<--- replace with your email

def get_password_from_env():
    # PASSWORD should be provided via GitHub Actions secret as env var PASSWORD
    pwd = os.environ.get("PASSWORD")
    if not pwd:
        raise SystemExit("❌ PASSWORD environment variable is required")
    return pwd

class GoogleLabsLogin:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.profile_path = os.path.join(os.getcwd(), "chrome_profile")
        os.makedirs(self.profile_path, exist_ok=True)
        self.setup_driver()

    def setup_driver(self):
        options = Options()
        options.add_argument(f"--user-data-dir={self.profile_path}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--headless=new")              # headless for CI
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Selenium 4.25+ uses Selenium Manager to auto-download the correct driver
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)
        print("✅ Chrome driver started with Selenium Manager!")

    def click_sign_in_button(self):
        print("🔍 Searching for Sign in button...")
        btn_xpaths = [
            "//button[contains(., 'Sign in with Google')]",
            "//span[contains(., 'Sign in with Google')]/ancestor::button",
            "//button[contains(., 'Sign in')]",
            "//a[contains(., 'Sign in')]",
        ]
        for xpath in btn_xpaths:
            try:
                btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(1)
                try:
                    btn.click()
                except:
                    self.driver.execute_script("arguments[0].click();", btn)
                print("✅ Clicked Sign in button.")
                return True
            except Exception:
                continue
        print("⚠️ Could not find Sign in button.")
        return False

    def login(self):
        print("🌐 Opening Google Labs login...")
        self.driver.get("https://labs.google/fx/tools/flow")
        time.sleep(2)

        if "sign in" not in self.driver.page_source.lower():
            print("✅ Already logged in.")
            return True

        if not self.click_sign_in_button():
            print("❌ Could not locate the sign-in button.")
            return False

        try:
            email_input = self.wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
            email_input.send_keys(self.email)
            email_input.send_keys(Keys.ENTER)
            print("📧 Email entered.")
            time.sleep(3)

            passwd_input = self.wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
            passwd_input.send_keys(self.password)
            passwd_input.send_keys(Keys.ENTER)
            print("🔒 Password entered.")

            time.sleep(8)
            print("✅ Logged in successfully.")
            return True

        except TimeoutException:
            print("❌ Timeout during login flow.")
            return False
        except Exception as e:
            print("❌ Login failed:", e)
            return False

    def save_cookies(self, filename="cookies.pkl", filename_json="cookies.json"):
        cookies = self.driver.get_cookies()
        with open(filename, "wb") as f:
            pickle.dump(cookies, f)
        with open(filename_json, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        print(f"✅ Cookies saved: {filename}, {filename_json}")

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    password = get_password_from_env()
    bot = GoogleLabsLogin(EMAIL, password)
    try:
        ok = bot.login()
        if ok:
            bot.save_cookies()
    finally:
        bot.close()
