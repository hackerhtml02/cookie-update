import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# --- Configuration ---
EMAIL = "muhammadharis8765@imagescraftai.live"  # your email
OUTPUT_FILE = "cookies.json"                    # output filename
# ----------------------

def get_password_from_env():
    pwd = os.environ.get("PASSWORD")
    if not pwd:
        raise SystemExit("❌ PASSWORD environment variable not found.")
    return pwd

class GoogleLabsLogin:
    def __init__(self, email, password, headless=True):
        self.email = email
        self.password = password
        self.headless = headless
        self.profile_path = os.path.join(os.getcwd(), "chrome_profile")
        os.makedirs(self.profile_path, exist_ok=True)
        self.setup_driver()

    def setup_driver(self):
        options = Options()
        options.add_argument(f"--user-data-dir={self.profile_path}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        if self.headless:
            options.add_argument("--headless=new")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # ✅ Selenium Manager handles driver automatically
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)
        print("✅ Chrome driver started (Selenium Manager).")

    def click_sign_in(self):
        """Try to click 'Sign in' or 'Sign in with Google' buttons."""
        xpaths = [
            "//button[contains(., 'Sign in with Google')]",
            "//span[contains(., 'Sign in with Google')]/ancestor::button",
            "//button[contains(., 'Sign in')]",
            "//a[contains(., 'Sign in')]",
        ]
        for xp in xpaths:
            try:
                btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                btn.click()
                return True
            except Exception:
                continue
        print("⚠️ Sign-in button not found.")
        return False

    def login(self):
        print("🌐 Opening Google Labs login page...")
        self.driver.get("https://labs.google/fx/tools/flow")
        time.sleep(2)

        if "sign in" not in self.driver.page_source.lower():
            print("✅ Already logged in.")
            return True

        if not self.click_sign_in():
            print("❌ Could not find sign-in button.")
            return False

        try:
            # Email
            email_input = self.wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
            email_input.send_keys(self.email)
            email_input.send_keys(Keys.ENTER)
            time.sleep(3)

            # Password
            passwd_input = self.wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
            passwd_input.send_keys(self.password)
            passwd_input.send_keys(Keys.ENTER)
            print("🔒 Credentials submitted.")

            time.sleep(8)
            return "sign in" not in self.driver.page_source.lower()
        except TimeoutException:
            print("❌ Timeout during login.")
            return False
        except Exception as e:
            print("❌ Login failed:", e)
            return False

    def format_labs_cookies(self, cookies):
        """Filter and format only labs.google cookies into your desired structure."""
        formatted = []
        i = 1
        for c in cookies:
            domain = c.get("domain", "")
            if "labs.google" not in domain:
                continue  # only keep labs.google cookies

            expiry = c.get("expiry")
            session = expiry is None
            host_only = not domain.startswith(".")
            same_site = c.get("sameSite", "unspecified").lower()
            if same_site not in ["lax", "strict", "none"]:
                same_site = "unspecified"

            item = {
                "domain": domain,
                **({"expirationDate": float(expiry)} if expiry else {}),
                "hostOnly": host_only,
                "httpOnly": bool(c.get("httpOnly")),
                "name": c.get("name"),
                "path": c.get("path", "/"),
                "sameSite": same_site,
                "secure": bool(c.get("secure")),
                "session": session,
                "storeId": "0",
                "value": c.get("value"),
                "id": i
            }
            formatted.append(item)
            i += 1

        return formatted

    def save_cookies(self, path):
        all_cookies = self.driver.get_cookies()
        labs_cookies = self.format_labs_cookies(all_cookies)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(labs_cookies, f, indent=4, ensure_ascii=False)

        print(f"✅ Saved {len(labs_cookies)} labs.google cookies → {path}")

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    password = get_password_from_env()
    bot = GoogleLabsLogin(EMAIL, password)
    try:
        if bot.login():
            bot.save_cookies(OUTPUT_FILE)
        else:
            print("❌ Login failed — cookies not saved.")
    finally:
        bot.close()
