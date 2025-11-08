# google_labs_token.py
# Email is hardcoded here (as requested).
# Password must be provided via environment variable PASSWORD or GOOGLE_PASSWORD.

import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

# -------------------------
# HARDCODED EMAIL (replace if you want)
# -------------------------
HARDCODE_EMAIL = "muhammadharis8765@imagescraftai.live"  # <- hardcoded email here
# -------------------------

def get_password():
    # prefer explicit PASSWORD env var, fall back to GOOGLE_PASSWORD
    pwd = os.getenv("PASSWORD") or os.getenv("GOOGLE_PASSWORD")
    if not pwd:
        print("❌ ERROR: Password not found in environment. Set PASSWORD or GOOGLE_PASSWORD.")
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
        options.add_argument("--disable-gpu")
        options.add_argument("--incognito")
        if self.headless:
            options.add_argument("--headless=new")

        # webdriver-manager will fetch a compatible chromedriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 30)
        # Print versions for debugging in Actions logs
        try:
            print("ChromeDriver:", self.driver.capabilities.get("browserVersion") or self.driver.capabilities)
        except Exception:
            pass
        print("✅ Chrome WebDriver started.")

    def setup_network_interception(self):
        js = """
        (function() {
            if (window.__capture_fetch_installed) return;
            window.__capture_fetch_installed = true;
            window.__capturedAuthToken = null;
            const originalFetch = window.fetch.bind(window);
            window.fetch = function() {
                const args = Array.from(arguments);
                const options = args[1] || {};
                try {
                    if (options.headers) {
                        const getHeader = (h) => (typeof options.headers.get === 'function') ? options.headers.get(h) : options.headers[h];
                        const val = getHeader('authorization') || getHeader('Authorization');
                        if (val) window.__capturedAuthToken = val;
                    }
                } catch (e) {}
                return originalFetch.apply(this, arguments);
            };
        })();
        """
        try:
            self.driver.execute_script(js)
            print("🛠️ Network interception installed.")
        except Exception as e:
            print("⚠️ Could not inject fetch wrapper:", e)

    def get_captured_token(self):
        try:
            token = self.driver.execute_script("return window.__capturedAuthToken || null;")
            if token and token.lower().startswith("bearer "):
                token = token.split(" ", 1)[1]
            return token
        except Exception:
            return None

    def open_labs_and_signin(self):
        self.driver.get("https://labs.google/fx/tools/flow")
        time.sleep(2)

        if "sign in" not in self.driver.page_source.lower():
            print("✅ Possibly already signed in / no sign-in prompt.")
            return True

        btn_xpaths = [
            "//button[contains(., 'Sign in with Google')]",
            "//span[contains(., 'Sign in with Google')]/ancestor::button",
            "//button[contains(., 'Sign in')]",
            "//a[contains(., 'Sign in')]",
            "//a[contains(., 'Sign in with Google')]",
        ]
        clicked = False
        for xp in btn_xpaths:
            try:
                el = self.wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                try:
                    el.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", el)
                clicked = True
                print("🔑 Clicked sign-in button:", xp)
                break
            except Exception:
                continue

        if not clicked:
            print("⚠️ Sign-in button not found; opening Google sign-in directly.")
            self.driver.get("https://accounts.google.com/v3/signin/identifier")
            time.sleep(2)

        try:
            email_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
            email_input.clear()
            email_input.send_keys(self.email)
            email_input.send_keys(Keys.ENTER)
            print("📧 Email entered.")
            time.sleep(2)

            passwd_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
            passwd_input.clear()
            passwd_input.send_keys(self.password)
            passwd_input.send_keys(Keys.ENTER)
            print("🔒 Password submitted.")
            time.sleep(3)
            return True
        except TimeoutException:
            print("❌ Login failed or 2FA required.")
            return False
        except Exception as e:
            print("❌ Exception during login:", e)
            return False

    def create_new_project_and_trigger_requests(self, prompt_text="cute cat"):
        try:
            self.setup_network_interception()
            selectors = [
                "//button[contains(text(),'New project')]",
                "//div[contains(text(),'New project')]",
                "button[data-testid='new-project-button']",
                "button[aria-label*='New project']"
            ]
            for sel in selectors:
                try:
                    el = self.wait.until(EC.element_to_be_clickable((By.XPATH, sel)))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
                    try:
                        el.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", el)
                    print("📁 Clicked 'New project' using:", sel)
                    break
                except Exception:
                    continue

            time.sleep(2)
            try:
                input_candidates = self.driver.find_elements(By.CSS_SELECTOR, "textarea, input[type='text']")
                if input_candidates:
                    el = input_candidates[0]
                    el.click()
                    el.clear()
                    el.send_keys(prompt_text)
                    el.send_keys(Keys.ENTER)
                    print("✏️ Prompt submitted:", prompt_text)
            except Exception as e:
                print("⚠️ Could not submit prompt:", e)

            print("⏳ Waiting up to 40s for token...")
            for _ in range(40):
                tok = self.get_captured_token()
                if tok:
                    print("🎯 Token captured.")
                    return tok
                time.sleep(1)
            print("❌ No token captured.")
            return None
        except Exception as e:
            print("❌ Error during trigger:", e)
            return None

    def run_and_get_token(self, prompt_text="cute cat"):
        try:
            if not self.open_labs_and_signin():
                print("❌ Sign-in failed.")
                return None
            time.sleep(3)
            if "labs.google" not in self.driver.current_url:
                self.driver.get("https://labs.google/fx/tools/flow")
                time.sleep(2)
            token = self.create_new_project_and_trigger_requests(prompt_text)
            if token:
                with open("bearer_token.txt", "w") as f:
                    f.write(token)
                print("💾 Token saved to bearer_token.txt")
                return token
            return None
        finally:
            self.close()

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    EMAIL = HARDCODE_EMAIL
    PASSWORD = get_password()
    print(f"Using email: {EMAIL}  (hardcoded in script)")
    extractor = GoogleLabsTokenExtractor(EMAIL, PASSWORD, headless=True)
    token = extractor.run_and_get_token(prompt_text="cute cat")
    if token:
        print("✅ Final Token:", token)
    else:
        print("❌ No token extracted.")
