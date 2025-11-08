# save_as: save_cookies_googlelabs_formatted.py
"""
Login to Google Labs, then save cookies in the extended format you showed.

- EMAIL is hard-coded (change below).
- PASSWORD must be provided via environment variable PASSWORD.
- Requires: selenium (4.25+ recommended)
    pip install selenium
"""

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

# -----------------------
# Configure these values
# -----------------------
EMAIL = "muhammadharis8765@imagescraftai.live"   # <-- replace if needed
OUTPUT_FILE = "cookies.json"
# -----------------------

def get_password_from_env():
    pw = os.environ.get("PASSWORD")
    if not pw:
        raise SystemExit("❌ PASSWORD environment variable is required (set it in GitHub Secrets or env).")
    return pw

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
        options.add_argument("--profile-directory=Default")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        if self.headless:
            options.add_argument("--headless=new")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Selenium 4.25+ will use Selenium Manager to provide the correct driver
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)
        print("✅ Chrome driver started (Selenium Manager). Headless =", self.headless)

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
                time.sleep(0.7)
                try:
                    btn.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", btn)
                print("✅ Clicked Sign in button.")
                return True
            except Exception:
                continue
        print("⚠️ Sign in button not found.")
        return False

    def login(self):
        print("🌐 Opening Google Labs...")
        self.driver.get("https://labs.google/fx/tools/flow")
        time.sleep(2)

        # Quick check: if page doesn't contain 'sign in' then maybe already logged in
        if "sign in" not in self.driver.page_source.lower():
            print("✅ Page does not show 'sign in' — might already be logged in.")
            return True

        if not self.click_sign_in_button():
            print("❌ Couldn't locate sign in button; aborting login.")
            return False

        try:
            # Enter email
            email_input = self.wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
            email_input.clear()
            email_input.send_keys(self.email)
            email_input.send_keys(Keys.ENTER)
            print("📧 Email entered.")
            time.sleep(2.5)

            # Enter password
            passwd_input = self.wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
            passwd_input.clear()
            passwd_input.send_keys(self.password)
            passwd_input.send_keys(Keys.ENTER)
            print("🔒 Password entered.")
            # wait a bit for redirect / auth
            time.sleep(6)
            # final check
            if "sign in" in self.driver.page_source.lower():
                print("⚠️ After submitting credentials, still see 'sign in' — login may have failed or 2FA required.")
                return False
            print("✅ Login flow completed (note: may still fail if 2FA/challenge present).")
            return True

        except TimeoutException:
            print("❌ Timeout during login flow.")
            return False
        except Exception as e:
            print("❌ Login exception:", e)
            return False

    def format_cookies_extended(self, raw_cookies):
        """
        Convert Selenium cookie dicts to the extended format you showed.
        Adds: expirationDate (float), hostOnly (bool), session (bool), storeId ("0"), id (int), sameSite ("unspecified"/value)
        """
        formatted = []
        next_id = 1
        for c in raw_cookies:
            # selenium cookie keys: name, value, domain, path, expiry (optional), secure, httpOnly, sameSite (maybe)
            domain = c.get("domain", "")
            expiry = c.get("expiry")  # usually int seconds since epoch
            if expiry is None:
                expirationDate = None
                session_flag = True
            else:
                # convert to float with fractional part for similarity
                expirationDate = float(expiry)
                session_flag = False

            # hostOnly = True when domain does NOT start with a dot (i.e., exact host)
            host_only = False
            d = domain.lstrip()
            if d.startswith("."):
                host_only = False
            else:
                host_only = True

            # sameSite: selenium may have 'sameSite' string or not; default to "unspecified"
            ss = c.get("sameSite")
            # Normalize common values
            if ss is None:
                sameSite_val = "unspecified"
            else:
                ss_lower = str(ss).lower()
                if ss_lower in ("lax", "strict", "none"):
                    sameSite_val = ss_lower
                else:
                    sameSite_val = "unspecified"

            formatted_cookie = {
                "domain": domain.lstrip("."),               # your example used no leading dot for labs.google entries
                # use 'expirationDate' like in your example, omit or set to null if session
                **({"expirationDate": expirationDate} if expirationDate is not None else {}),
                "hostOnly": bool(host_only),
                "httpOnly": bool(c.get("httpOnly", False)),
                "name": c.get("name"),
                "path": c.get("path", "/"),
                "sameSite": sameSite_val,
                "secure": bool(c.get("secure", False)),
                "session": bool(session_flag),
                "storeId": "0",
                "value": c.get("value"),
                "id": next_id
            }
            formatted.append(formatted_cookie)
            next_id += 1

        return formatted

    def save_cookies_formatted(self, out_file=OUTPUT_FILE):
        raw = self.driver.get_cookies()
        formatted = self.format_cookies_extended(raw)
        # Save pretty JSON
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(formatted, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(formatted)} cookies to {out_file}")

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

# -----------------------
# Main execution
# -----------------------
if __name__ == "__main__":
    password = get_password_from_env()
    bot = GoogleLabsLogin(EMAIL, password, headless=True)  # set headless=False for debugging locally
    try:
        ok = bot.login()
        if ok:
            bot.save_cookies_formatted(OUTPUT_FILE)
        else:
            print("❌ Login did not succeed; cookies not saved.")
    finally:
        bot.close()
