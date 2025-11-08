# google_labs_token.py
# Email is hardcoded here (as requested).
# Password must be provided via environment variable PASSWORD or GOOGLE_PASSWORD.
#
# Usage:
# - Ensure dependencies: selenium, webdriver-manager
#   pip install selenium webdriver-manager
# - Set env var PASSWORD or GOOGLE_PASSWORD (do NOT hardcode your password)
# - Run: python google_labs_token.py

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
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException

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
    def __init__(self, email, password, headless=True, implicit_wait=5):
        self.email = email
        self.password = password
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.setup_driver()

    def setup_driver(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--incognito")
        # headless appropriate for CI (GitHub Actions)
        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
        # Start driver using webdriver-manager (auto-download matching chromedriver)
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(self.implicit_wait)
        self.wait = WebDriverWait(self.driver, 30)
        # Print capability info for debugging
        try:
            caps = self.driver.capabilities
            print("Browser capabilities:", caps)
        except Exception:
            pass
        print("✅ Chrome WebDriver started.")

    def setup_network_interception(self):
        # Inject JS fetch wrapper to capture Authorization header
        js = """
        (function() {
            if (window.__capture_fetch_installed) return;
            window.__capture_fetch_installed = true;
            window.__capturedAuthToken = null;
            const originalFetch = window.fetch.bind(window);
            window.fetch = function() {
                try {
                    const args = Array.prototype.slice.call(arguments);
                    const options = args[1] || {};
                    if (options && options.headers) {
                        try {
                            if (typeof options.headers.get === 'function') {
                                const val = options.headers.get('authorization') || options.headers.get('Authorization');
                                if (val) window.__capturedAuthToken = val;
                            } else {
                                for (let h in options.headers) {
                                    if (h.toLowerCase().includes('authorization')) {
                                        window.__capturedAuthToken = options.headers[h];
                                    }
                                }
                            }
                        } catch (e) {}
                    }
                } catch (err) {}
                return originalFetch.apply(this, arguments);
            };
            // Also try to capture X-Goog-AuthUser or other headers from XMLHttpRequest
            (function(open) {
                XMLHttpRequest.prototype.open = function() { this.addEventListener('readystatechange', function(){});
                    return open.apply(this, arguments);
                };
            })(XMLHttpRequest.prototype.open);
        })();
        """
        try:
            self.driver.execute_script(js)
            print("🛠️ Network interception installed (fetch wrapper).")
        except Exception as e:
            print("⚠️ Could not inject fetch wrapper:", e)

    def get_captured_token(self):
        # read the JS var set by our injected wrapper
        try:
            token = self.driver.execute_script("return window.__capturedAuthToken || null;")
            if token:
                token = token.strip()
                if token.lower().startswith("bearer "):
                    token = token.split(" ", 1)[1].strip()
                return token
            return None
        except Exception:
            return None

    def open_labs_and_signin(self):
        # go to Google Labs
        self.driver.get("https://labs.google/fx/tools/flow")
        time.sleep(2)  # let initial scripts load

        # If page doesn't show sign in, maybe accessible already
        if "sign in" not in self.driver.page_source.lower():
            print("✅ Page doesn't show 'sign in' — maybe already accessible.")
            return True

        # Try to click a Sign in / Sign in with Google button — multiple xpaths to be robust
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
                self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
                time.sleep(0.5)
                try:
                    el.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", el)
                clicked = True
                print("✅ Clicked sign-in button (xpath):", xp)
                break
            except Exception:
                continue

        if not clicked:
            print("⚠️ Could not find a Sign in button on Labs page; trying to open Google sign-in directly.")
            # fallback: open Google OAuth sign-in endpoint to force login
            self.driver.get("https://accounts.google.com/v3/signin/identifier")
            time.sleep(2)

        # Now perform Google email/password flow
        try:
            # email
            email_locators = [
                (By.ID, "identifierId"),
                (By.NAME, "identifier"),
                (By.CSS_SELECTOR, "input[type='email']"),
            ]
            email_input = None
            for loc in email_locators:
                try:
                    email_input = self.wait.until(EC.presence_of_element_located(loc))
                    if email_input:
                        break
                except Exception:
                    continue

            if not email_input:
                print("❌ Could not find email input.")
                return False

            email_input.clear()
            email_input.send_keys(self.email)
            email_input.send_keys(Keys.ENTER)
            print("📧 Email entered.")
            time.sleep(2)

            # password
            password_locators = [
                (By.NAME, "password"),
                (By.NAME, "Passwd"),
                (By.CSS_SELECTOR, "input[type='password']"),
            ]
            passwd_input = None
            for loc in password_locators:
                try:
                    passwd_input = self.wait.until(EC.presence_of_element_located(loc))
                    if passwd_input:
                        break
                except TimeoutException:
                    continue

            if not passwd_input:
                print("⚠️ Password input not immediately available; waiting longer (possible 2FA).")
                try:
                    passwd_input = WebDriverWait(self.driver, 60).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
                    )
                except Exception:
                    print("❌ Unable to find password field. Manual 2FA may be required.")
                    return False

            passwd_input.clear()
            passwd_input.send_keys(self.password)
            passwd_input.send_keys(Keys.ENTER)
            print("🔒 Password submitted.")
            time.sleep(3)
            return True

        except Exception as e:
            print("❌ Exception during sign-in:", e)
            return False

    def _hide_overlays(self):
        # Try to hide elements that might overlap the input (iframes, modals, overlays)
        js = """
        (function(){
            // Hide common overlays (iframes, modals, and elements with dialog/overlay roles)
            const hideSelectors = ['iframe', '.modal', '.overlay', '[role=\"dialog\"]', '[aria-modal=\"true\"]'];
            hideSelectors.forEach(s => {
                document.querySelectorAll(s).forEach(e => {
                    try {
                        // keep display none but leave in DOM
                        e.style.pointerEvents = 'none';
                        e.style.opacity = '0';
                        e.style.visibility = 'hidden';
                        e.style.zIndex = '-99999';
                    } catch (err) {}
                });
            });
            // remove known changelog iframe if present by src pattern
            document.querySelectorAll('iframe').forEach(f => {
                try {
                    if (f.src && f.src.includes('changelogs')) {
                        f.style.display = 'none';
                        f.style.pointerEvents = 'none';
                    }
                } catch(e) {}
            });
            return true;
        })();
        """
        try:
            self.driver.execute_script(js)
            print("🧹 Hidden potential overlays/iframes blocking the prompt field.")
        except Exception:
            pass

    def _safe_set_value_and_submit(self, el, text):
        # Scroll into view & set value using JS to avoid click interception
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", el)
            # focus element
            self.driver.execute_script("arguments[0].focus();", el)
            # set value (works for textarea/input)
            self.driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", el, text)
            time.sleep(0.3)
            # Try pressing Enter to submit if that triggers request
            try:
                el.send_keys(Keys.ENTER)
            except Exception:
                # fallback: dispatch keyboard event via JS
                self.driver.execute_script("""
                    var ev = new KeyboardEvent('keydown', {key: 'Enter', keyCode:13, which:13, bubbles:true});
                    arguments[0].dispatchEvent(ev);
                """, el)
            print("✏️ Prompt submitted safely via JS injection.")
            return True
        except Exception as e:
            print("⚠️ _safe_set_value_and_submit error:", e)
            return False

    def create_new_project_and_trigger_requests(self, prompt_text="cute cat"):
        # Ensure Labs main UI loaded and trigger a request by submitting a prompt
        try:
            # install fetch wrapper first so subsequent calls include header capture
            self.setup_network_interception()

            # Click 'New project' if exists
            selectors = [
                "//button[contains(text(),'New project')]",
                "//div[contains(text(),'New project')]",
                "button[data-testid='new-project-button']",
                "button[aria-label*='New project']"
            ]
            clicked = False
            for sel in selectors:
                try:
                    if sel.startswith("//"):
                        el = self.wait.until(EC.element_to_be_clickable((By.XPATH, sel)))
                    else:
                        el = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
                    time.sleep(0.4)
                    try:
                        el.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", el)
                    clicked = True
                    print("✅ New project clicked using:", sel)
                    break
                except Exception:
                    continue

            if not clicked:
                print("⚠️ Couldn't click 'New project' — attempting to open labs main page directly to trigger requests.")
            # Wait a moment for the UI to render
            time.sleep(2)

            # Hide overlays that might intercept clicks
            self._hide_overlays()
            time.sleep(0.5)

            # Look for textarea/input for prompt; attempt multiple strategies
            input_selectors = [
                "textarea[placeholder]",                # common textarea with placeholder
                "textarea",                             # any textarea
                "div[contenteditable='true']",          # sometimes editors are contenteditable divs
                "input[type='text']"
            ]

            prompt_set = False
            # 1) try CSS selectors
            for sel in input_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if elements:
                        # choose first visible & enabled element
                        for el in elements:
                            try:
                                if el.is_displayed() and el.is_enabled():
                                    if self._safe_set_value_and_submit(el, prompt_text):
                                        prompt_set = True
                                        break
                            except Exception:
                                continue
                        if prompt_set:
                            break
                except Exception:
                    continue

            # 2) As fallback, try XPath that matches likely editor textareas
            if not prompt_set:
                try:
                    xpath_candidates = [
                        "//textarea",
                        "//div[@contenteditable='true']",
                        "//input[@type='text']"
                    ]
                    for xp in xpath_candidates:
                        try:
                            els = self.driver.find_elements(By.XPATH, xp)
                            if els:
                                for el in els:
                                    try:
                                        if el.is_displayed() and el.is_enabled():
                                            if self._safe_set_value_and_submit(el, prompt_text):
                                                prompt_set = True
                                                break
                                    except Exception:
                                        continue
                                if prompt_set:
                                    break
                        except Exception:
                            continue
                except Exception:
                    pass

            if not prompt_set:
                print("⚠️ No suitable prompt input found or could not set prompt; requests may still fire from UI interactions.")

            # Wait for requests to fire & token to be captured
            print("⏳ Waiting up to 40s for token to appear...")
            for i in range(40):
                tok = self.get_captured_token()
                if tok:
                    print("🎯 Token captured.")
                    return tok
                time.sleep(1)

            print("❌ No token captured after prompt trigger.")
            return None

        except Exception as e:
            print("❌ Error in create_new_project_and_trigger_requests:", e)
            return None

    def run_and_get_token(self, prompt_text="cute cat"):
        try:
            if not self.open_labs_and_signin():
                print("❌ Sign-in failed.")
                return None

            # after sign-in, ensure we are back on labs page
            time.sleep(3)
            try:
                if "labs.google" not in self.driver.current_url:
                    self.driver.get("https://labs.google/fx/tools/flow")
                    time.sleep(3)
            except Exception:
                pass

            token = self.create_new_project_and_trigger_requests(prompt_text)
            if token:
                try:
                    with open("bearer_token.txt", "w") as f:
                        f.write(token)
                    print("💾 Token saved to bearer_token.txt")
                except Exception:
                    pass
                return token
            return None
        finally:
            # Clean up: delete cookies to avoid accidental persistence, then quit
            try:
                self.driver.delete_all_cookies()
            except Exception:
                pass
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
