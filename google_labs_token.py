# google_labs_token.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import os, time

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

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 30)
        print("✅ Chrome WebDriver started successfully.")

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
                if (options.headers) {
                    const getHeader = (h) => (typeof options.headers.get === 'function') ? options.headers.get(h) : options.headers[h];
                    const val = getHeader('authorization') || getHeader('Authorization');
                    if (val) window.__capturedAuthToken = val;
                }
                return originalFetch.apply(this, arguments);
            };
        })();
        """
        self.driver.execute_script(js)
        print("🛠️ Network interception (fetch wrapper) installed.")

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
            print("✅ Already signed in or no sign-in prompt.")
            return True

        # Try to click sign in button
        for xp in [
            "//button[contains(., 'Sign in with Google')]",
            "//span[contains(., 'Sign in with Google')]/ancestor::button",
            "//button[contains(., 'Sign in')]",
            "//a[contains(., 'Sign in')]"
        ]:
            try:
                el = self.wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                el.click()
                print("🔑 Clicked Sign In button.")
                break
            except Exception:
                continue

        # Perform email and password login
        try:
            email_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
            email_input.send_keys(self.email)
            email_input.send_keys(Keys.ENTER)
            print("📧 Email entered.")
            time.sleep(2)

            passwd_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
            passwd_input.send_keys(self.password)
            passwd_input.send_keys(Keys.ENTER)
            print("🔒 Password submitted.")
            time.sleep(3)
            return True
        except TimeoutException:
            print("❌ Login failed or 2FA required.")
            return False

    def create_new_project_and_trigger_requests(self, prompt_text="cute cat"):
        try:
            self.setup_network_interception()
            # Try clicking 'New project'
            for sel in [
                "//button[contains(text(),'New project')]",
                "button[data-testid='new-project-button']",
            ]:
                try:
                    el = self.wait.until(EC.element_to_be_clickable((By.XPATH, sel)))
                    el.click()
                    print("📁 Clicked 'New project'.")
                    break
                except Exception:
                    continue

            # Try typing prompt
            try:
                input_field = self.driver.find_element(By.CSS_SELECTOR, "textarea, input[type='text']")
                input_field.send_keys(prompt_text)
                input_field.send_keys(Keys.ENTER)
                print(f"✏️ Prompt entered: {prompt_text}")
            except Exception:
                print("⚠️ Could not find input field for prompt.")

            # Wait for token
            print("⏳ Waiting for token...")
            for _ in range(40):
                tok = self.get_captured_token()
                if tok:
                    print("🎯 Token captured!")
                    return tok
                time.sleep(1)
            return None
        except Exception as e:
            print("❌ Error capturing token:", e)
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
            print("❌ No token captured.")
            return None
        finally:
            self.close()

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    EMAIL = "muhammadharis8765@imagescraftai.live"
    PASSWORD = os.getenv("PASSWORD")
    if not EMAIL or not PASSWORD:
        print("❌ Please set EMAIL and PASSWORD environment variables.")
        exit(1)

    extractor = GoogleLabsTokenExtractor(EMAIL, PASSWORD, headless=True)
    token = extractor.run_and_get_token(prompt_text="cute cat")
    if token:
        print("✅ Final Token:", token)
    else:
        print("❌ No token extracted.")
