# google_labs_token_network_debug.py
# Enhanced network-debugging Google Labs token extractor (modified to include "textarea, input[type='text']" selector)
#
# - Email is hardcoded below (change if needed)
# - Password must be provided via env var PASSWORD or GOOGLE_PASSWORD
# - Script tries to capture Authorization headers from fetch/XHR/WebSocket and saves
#   a network_debug.json and bearer_token.txt (if found).
#
# Usage:
#   export PASSWORD="your_password_here"
#   python google_labs_token_network_debug.py

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
from selenium.common.exceptions import TimeoutException

# -------------------------
# HARDCODED EMAIL (replace if you want)
# -------------------------
HARDCODE_EMAIL = "muhammadharis8765@imagescraftai.live"
# -------------------------

def get_password():
    pwd = os.getenv("PASSWORD") or os.getenv("GOOGLE_PASSWORD")
    if not pwd:
        print("❌ ERROR: Password not found in environment. Set PASSWORD or GOOGLE_PASSWORD.")
        sys.exit(1)
    return pwd

class GoogleLabsNetworkDebugger:
    def __init__(self, email, password, headless=True, implicit_wait=5):
        self.email = email
        self.password = password
        self.headless = headless
        self.implicit_wait = implicit_wait
        self._start_driver()

    def _start_driver(self):
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
        self.driver.implicitly_wait(self.implicit_wait)
        self.wait = WebDriverWait(self.driver, 30)
        try:
            print("Browser capabilities:", self.driver.capabilities)
        except Exception:
            pass
        print("✅ Chrome WebDriver started.")

    def inject_network_debugger(self):
        # JS that wraps fetch, XHR and WebSocket to record outgoing requests/headers
        js = r"""
        (function(){
            if (window.__network_debug_installed) return;
            window.__network_debug_installed = true;
            window.__network_debug = window.__network_debug || [];
            window.__capturedAuthToken = window.__capturedAuthToken || null;

            function normalizeHeaders(h) {
                const out = {};
                try {
                    if (!h) return out;
                    if (typeof h.forEach === 'function' && typeof h.get === 'function') {
                        // Headers object
                        h.forEach((v,k) => out[k] = v);
                    } else if (typeof h === 'object') {
                        for (const k in h) {
                            try { out[k] = h[k]; } catch(e) {}
                        }
                    }
                } catch(e){}
                return out;
            }

            function record(obj) {
                try {
                    obj.ts = (new Date()).toISOString();
                    window.__network_debug.push(obj);
                    // also check for auth header presence
                    const headers = obj.headers || {};
                    for (const k in headers) {
                        if (k.toLowerCase().includes('authorization')) {
                            try {
                                window.__capturedAuthToken = headers[k];
                            } catch(e){}
                        }
                    }
                    // quick body scan for tokens
                    if (obj.body && typeof obj.body === 'string') {
                        const b = obj.body;
                        if (b.includes('access_token') || b.includes('id_token') || b.includes('Authorization') || b.includes('bearer')) {
                            window.__capturedAuthToken = window.__capturedAuthToken || b;
                        }
                    }
                } catch(e){}
            }

            // wrap fetch
            const origFetch = window.fetch;
            window.fetch = function(input, init) {
                try {
                    const url = (typeof input === 'string') ? input : (input && input.url) || '';
                    const headers = normalizeHeaders(init && init.headers);
                    const body = init && init.body;
                    record({type:'fetch', url: String(url), headers: headers, body: (body && (typeof body === 'string' ? body : JSON.stringify(body)))});
                } catch(e){}
                return origFetch.apply(this, arguments);
            };

            // wrap XMLHttpRequest
            (function() {
                const origOpen = XMLHttpRequest.prototype.open;
                const origSend = XMLHttpRequest.prototype.send;
                const origSetReqHeader = XMLHttpRequest.prototype.setRequestHeader;
                XMLHttpRequest.prototype._headers = {};
                XMLHttpRequest.prototype.setRequestHeader = function(k, v) {
                    try {
                        this._headers = this._headers || {};
                        this._headers[k] = v;
                    } catch(e){}
                    return origSetReqHeader.apply(this, arguments);
                };
                XMLHttpRequest.prototype.open = function(method, url) {
                    try { this._method = method; this._url = url; } catch(e){}
                    return origOpen.apply(this, arguments);
                };
                XMLHttpRequest.prototype.send = function(body) {
                    try {
                        const headers = this._headers || {};
                        const b = (typeof body === 'string') ? body : (body ? JSON.stringify(body) : null);
                        record({type:'xhr', method: this._method, url: this._url, headers: headers, body: b});
                    } catch(e){}
                    return origSend.apply(this, arguments);
                };
            })();

            // wrap WebSocket.send to log outgoing messages
            (function() {
                const OrigWS = window.WebSocket;
                function WrappedWebSocket(url, protocols) {
                    const ws = protocols ? new OrigWS(url, protocols) : new OrigWS(url);
                    const origSend = ws.send;
                    ws.send = function(data) {
                        try {
                            record({type:'websocket', url: url, message: (typeof data === 'string' ? data : JSON.stringify(data))});
                        } catch(e){}
                        return origSend.apply(this, arguments);
                    };
                    return ws;
                }
                WrappedWebSocket.prototype = OrigWS.prototype;
                window.WebSocket = WrappedWebSocket;
            })();

            // expose helper to get cookies and performance entries
            window.__network_debug_dump = function(){
                try {
                    return {
                        debug: window.__network_debug || [],
                        token: window.__capturedAuthToken || null,
                        cookies: document.cookie || "",
                        perf: (window.performance && typeof window.performance.getEntries === 'function') ? window.performance.getEntries().map(e=>({name:e.name, entryType:e.entryType, startTime:e.startTime, duration:e.duration})) : []
                    };
                } catch(e){ return {debug: window.__network_debug||[], token: window.__capturedAuthToken||null, cookies:""}; }
            };
        })();
        """
        try:
            self.driver.execute_script(js)
            print("🛠️ Injected network debugger (fetch/XHR/WebSocket).")
        except Exception as e:
            print("⚠️ Could not inject network debugger:", e)

    def open_labs_and_signin(self):
        self.driver.get("https://labs.google/fx/tools/flow")
        time.sleep(2)
        # If sign-in not shown, maybe already access
        if "sign in" not in self.driver.page_source.lower():
            print("✅ No sign-in prompt detected (page may be reachable).")
            return True

        # try click sign-in
        btn_xpaths = [
            "//button[contains(., 'Sign in with Google')]",
            "//span[contains(., 'Sign in with Google')]/ancestor::button",
            "//button[contains(., 'Sign in')]",
            "//a[contains(., 'Sign in')]"
        ]
        clicked = False
        for xp in btn_xpaths:
            try:
                el = self.wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
                time.sleep(0.3)
                try:
                    el.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", el)
                clicked = True
                print("✅ Clicked sign-in button:", xp)
                break
            except Exception:
                continue

        if not clicked:
            print("⚠️ Sign-in button not found; opening Google sign-in directly.")
            self.driver.get("https://accounts.google.com/v3/signin/identifier")
            time.sleep(2)

        # fill email
        try:
            email_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
            email_input.clear()
            email_input.send_keys(self.email)
            email_input.send_keys(Keys.ENTER)
            print("📧 Email entered.")
            time.sleep(2)
        except Exception as e:
            print("❌ Could not find or fill email input:", e)
            return False

        # fill password
        try:
            passwd_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
            passwd_input.clear()
            passwd_input.send_keys(self.password)
            passwd_input.send_keys(Keys.ENTER)
            print("🔒 Password submitted.")
            time.sleep(3)
            return True
        except Exception as e:
            print("❌ Could not find or fill password input (2FA or page change?):", e)
            return False

    def hide_overlays(self):
        js = """
        (function(){
            try {
                document.querySelectorAll('iframe, .modal, .overlay, [role=\"dialog\"]').forEach(e=>{
                    try {
                        e.style.pointerEvents='none';
                        e.style.opacity='0';
                        e.style.visibility='hidden';
                        e.style.zIndex='-999999';
                    } catch(e){}
                });
            } catch(e){}
            return true;
        })();
        """
        try:
            self.driver.execute_script(js)
        except Exception:
            pass

    def click_new_project_and_submit_prompt(self, prompt_text="cute cat"):
        # click new project
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
                time.sleep(0.3)
                try:
                    el.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", el)
                clicked = True
                print("✅ New project clicked using:", sel)
                break
            except Exception:
                continue

        time.sleep(2)
        # hide overlays
        self.hide_overlays()
        time.sleep(0.5)

        # try multiple input strategies (textarea, contenteditable, input)
        tried = []
        success = False
        # <-- inserted "textarea, input[type='text']" here (in-between)
        css_candidates = [
            "textarea[placeholder]",
            "textarea, input[type='text']",
            "textarea",
            "div[contenteditable='true']",
            "input[type='text']"
        ]
        for sel in css_candidates:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for el in els:
                    try:
                        if not el.is_displayed() or not el.is_enabled():
                            continue
                        # set via JS to avoid click interception
                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].focus();", el)
                        # set value & dispatch input event
                        self.driver.execute_script(
                            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));",
                            el, prompt_text
                        )
                        time.sleep(0.2)
                        try:
                            el.send_keys(Keys.ENTER)
                        except Exception:
                            # dispatch Enter key via JS
                            self.driver.execute_script("""
                                var ev = new KeyboardEvent('keydown', {key:'Enter', keyCode:13, which:13, bubbles:true});
                                arguments[0].dispatchEvent(ev);
                            """, el)
                        print("✏️ Prompt set in element selector:", sel)
                        success = True
                        break
                    except Exception:
                        continue
                if success:
                    break
            except Exception:
                continue

        # xpath fallback
        if not success:
            xpath_candidates = ["//textarea", "//div[@contenteditable='true']", "//input[@type='text']"]
            for xp in xpath_candidates:
                try:
                    els = self.driver.find_elements(By.XPATH, xp)
                    for el in els:
                        try:
                            if not el.is_displayed() or not el.is_enabled():
                                continue
                            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].focus();", el)
                            self.driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", el, prompt_text)
                            time.sleep(0.2)
                            try:
                                el.send_keys(Keys.ENTER)
                            except Exception:
                                self.driver.execute_script("""
                                    var ev = new KeyboardEvent('keydown', {key:'Enter', keyCode:13, which:13, bubbles:true});
                                    arguments[0].dispatchEvent(ev);
                                """, el)
                            print("✏️ Prompt set in element xpath:", xp)
                            success = True
                            break
                        except Exception:
                            continue
                    if success:
                        break
                except Exception:
                    continue

        if not success:
            print("⚠️ Could not find a visible editable element to set the prompt. UI may have changed.")
        return success

    def fetch_network_debug_dump(self):
        try:
            dump = self.driver.execute_script("return window.__network_debug_dump ? window.__network_debug_dump() : {debug:[], token:null, cookies:document.cookie, perf:[]};")
            return dump
        except Exception as e:
            print("⚠️ Error fetching network debug dump:", e)
            return {"debug": [], "token": None, "cookies": "", "perf": []}

    def save_debug_files(self, dump, filename_prefix="network_debug"):
        # dump network info to JSON
        try:
            fname = f"{filename_prefix}.json"
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(dump, f, indent=2, ensure_ascii=False)
            print(f"💾 Network debug saved to {fname}")
        except Exception as e:
            print("⚠️ Could not save network debug JSON:", e)

        # Save token if present
        token = dump.get("token") or None
        if token:
            tt = str(token).strip()
            if tt.lower().startswith("bearer "):
                tt = tt.split(" ", 1)[1].strip()
            try:
                with open("bearer_token.txt", "w", encoding="utf-8") as f:
                    f.write(tt)
                print("🔐 Extracted token saved to bearer_token.txt")
            except Exception as e:
                print("⚠️ Could not save bearer_token.txt:", e)
        else:
            print("ℹ️ No token found in dump.token")

    def save_cookies_file(self, filename="cookies.json"):
        try:
            cookies = self.driver.get_cookies()
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            print(f"💾 Cookies saved to {filename}")
        except Exception as e:
            print("⚠️ Could not save cookies:", e)

    def run(self, prompt_text="cute cat", wait_for_seconds=20):
        try:
            # inject interceptor
            self.inject_network_debugger()

            # open and sign in
            ok = self.open_labs_and_signin()
            if not ok:
                print("❌ Sign-in failed — aborting.")
                return None

            # ensure back to labs page
            time.sleep(2)
            try:
                if "labs.google" not in self.driver.current_url:
                    self.driver.get("https://labs.google/fx/tools/flow")
                    time.sleep(2)
            except Exception:
                pass

            # give time for UI to render and JS to initialize
            time.sleep(1)
            # Click new project and set prompt
            _ = self.click_new_project_and_submit_prompt(prompt_text=prompt_text)

            # wait for outgoing requests to run
            print(f"⏳ Waiting up to {wait_for_seconds}s for network activity...")
            time.sleep(wait_for_seconds)

            # fetch dump
            dump = self.fetch_network_debug_dump()

            # augment dump with driver cookies and performance entries (if not included)
            try:
                dump["_driver_cookies"] = self.driver.get_cookies()
            except Exception:
                pass

            # save debug and cookies
            self.save_debug_files(dump, filename_prefix="network_debug")
            self.save_cookies_file(filename="cookies.json")

            # also write a short summary text file
            try:
                summary = {
                    "found_token": bool(dump.get("token")),
                    "token_preview": (dump.get("token")[:200] + "...") if dump.get("token") and len(str(dump.get("token"))) > 200 else dump.get("token"),
                    "entries_count": len(dump.get("debug", []))
                }
                with open("network_summary.json", "w", encoding="utf-8") as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
                print("💾 network_summary.json saved.")
            except Exception:
                pass

            return dump
        finally:
            try:
                self.driver.quit()
            except Exception:
                pass

if __name__ == "__main__":
    PASSWORD = get_password()
    print(f"Using email: {HARDCODE_EMAIL}  (hardcoded in script)")
    dbg = GoogleLabsNetworkDebugger(HARDCODE_EMAIL, PASSWORD, headless=True)
    result = dbg.run(prompt_text="cute cat", wait_for_seconds=20)
    if result and result.get("token"):
        print("✅ Token captured (see bearer_token.txt).")
    else:
        print("❌ No token captured. Check network_debug.json and cookies.json for details.")
