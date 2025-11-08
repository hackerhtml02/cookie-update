# google_labs_token_network_debug.py
# Enhanced Google Labs Token Extractor
# Saves cookies.json immediately after Google login and uploads artifacts safely

import os, time, json, sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

HARDCODE_EMAIL = "muhammadharis8765@imagescraftai.live"

def get_password():
    pwd = os.getenv("PASSWORD") or os.getenv("GOOGLE_PASSWORD")
    if not pwd:
        print("❌ ERROR: Password not found in environment. Set PASSWORD or GOOGLE_PASSWORD.")
        sys.exit(1)
    return pwd

class GoogleLabsNetworkDebugger:
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
            opts.add_argument("--disable-gpu")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opts)
        self.wait = WebDriverWait(self.driver, 30)
        print("✅ Chrome WebDriver started.")

    def save_cookies(self):
        try:
            cookies = self.driver.get_cookies()
            with open("cookies.json", "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            print("💾 Cookies saved to cookies.json")
        except Exception as e:
            print("⚠️ Could not save cookies:", e)

    def open_and_signin(self):
        self.driver.get("https://labs.google/fx/tools/flow")
        time.sleep(2)
        if "sign in" not in self.driver.page_source.lower():
            print("✅ No sign-in required.")
            self.save_cookies()
            return True

        btns = [
            "//button[contains(., 'Sign in with Google')]",
            "//span[contains(., 'Sign in with Google')]/ancestor::button",
            "//button[contains(., 'Sign in')]",
            "//a[contains(., 'Sign in')]"
        ]
        for xp in btns:
            try:
                el = self.wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                el.click()
                print("🔑 Clicked sign-in:", xp)
                break
            except Exception:
                continue

        try:
            email_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
            email_input.clear()
            email_input.send_keys(self.email)
            email_input.send_keys(Keys.ENTER)
            print("📧 Email entered.")
            time.sleep(2)
        except Exception as e:
            print("❌ Email field error:", e)
            return False

        try:
            pwd_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
            pwd_input.clear()
            pwd_input.send_keys(self.password)
            pwd_input.send_keys(Keys.ENTER)
            print("🔒 Password submitted.")
            time.sleep(3)
            self.save_cookies()  # ✅ Save cookies after successful login
            return True
        except Exception as e:
            print("❌ Password field error:", e)
            return False

    def inject_debugger(self):
        js = """
        (function(){
            if(window.__network_debug_installed)return;
            window.__network_debug_installed=true;
            window.__capturedAuthToken=null;
            window.__network_debug=[];
            const origFetch=window.fetch;
            window.fetch=function(u,o){
                try{
                    if(o&&o.headers){
                        for(const k in o.headers){
                            if(k.toLowerCase().includes('authorization')){
                                window.__capturedAuthToken=o.headers[k];
                            }
                        }
                    }
                    window.__network_debug.push({url:u,headers:o?o.headers:null});
                }catch(e){}
                return origFetch.apply(this,arguments);
            };
            window.__network_debug_dump=function(){
                return {token:window.__capturedAuthToken,debug:window.__network_debug,cookies:document.cookie};
            };
        })();
        """
        self.driver.execute_script(js)
        print("🛠️ Debugger injected.")

    def run(self, prompt_text="cute cat"):
        try:
            self.inject_debugger()
            if not self.open_and_signin():
                print("❌ Sign-in failed.")
                return None
            time.sleep(3)
            if "labs.google" not in self.driver.current_url:
                self.driver.get("https://labs.google/fx/tools/flow")
                time.sleep(3)
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "textarea, input[type='text']")
            if inputs:
                el = inputs[0]
                self.driver.execute_script(
                    "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input',{bubbles:true}));",
                    el, prompt_text
                )
                el.send_keys(Keys.ENTER)
                print("✏️ Prompt submitted.")
            else:
                print("⚠️ No text area found.")
            time.sleep(15)
            dump = self.driver.execute_script("return window.__network_debug_dump ? window.__network_debug_dump() : {};")
            with open("network_debug.json", "w", encoding="utf-8") as f:
                json.dump(dump, f, indent=2, ensure_ascii=False)
            print("💾 network_debug.json saved.")
            token = dump.get("token")
            if token:
                with open("bearer_token.txt", "w") as f:
                    f.write(token)
                print("✅ Token saved to bearer_token.txt")
            else:
                print("❌ No token captured.")
        finally:
            try:
                self.driver.quit()
            except Exception:
                pass

if __name__ == "__main__":
    PASSWORD = get_password()
    print(f"Using email: {HARDCODE_EMAIL} (hardcoded)")
    GoogleLabsNetworkDebugger(HARDCODE_EMAIL, PASSWORD, headless=True).run()
