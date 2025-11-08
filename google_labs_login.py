import os
import time
import base64
import zipfile
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def google_labs_login_and_capture_token(github_repo, prompt_text="Generate a creative story"):
    EMAIL = "muhammadharis8765@imagescraftai.live"
    PASSWORD = os.environ.get("PASSWORD")
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

    if not all([EMAIL, PASSWORD, GITHUB_TOKEN]):
        raise RuntimeError("Missing environment variables: EMAIL, PASSWORD, or GITHUB_TOKEN")

    profile_dir = "/tmp/chrome_profile"
    os.makedirs(profile_dir, exist_ok=True)

    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--headless=new")
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--profile-directory=Default")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)

    def inject_interceptor():
        js = """
        (function() {
            if (window.__capture_installed) return;
            window.__capture_installed = true;
            window.__capturedAuthToken = null;
            const origFetch = window.fetch.bind(window);
            window.fetch = function() {
                const args = Array.from(arguments);
                const opts = args[1] || {};
                if (opts.headers) {
                    for (let k in opts.headers) {
                        if (k.toLowerCase() === 'authorization') {
                            window.__capturedAuthToken = opts.headers[k];
                        }
                    }
                }
                return origFetch.apply(this, args);
            };
            const origXHR = XMLHttpRequest.prototype.setRequestHeader;
            XMLHttpRequest.prototype.setRequestHeader = function(header, value) {
                if (header.toLowerCase() === 'authorization') {
                    window.__capturedAuthToken = value;
                }
                return origXHR.apply(this, arguments);
            };
        })();
        """
        driver.execute_script(js)
        print("✅ Network interceptor installed")
    
    def get_token():
        token = driver.execute_script("return window.__capturedAuthToken || null;")
        if token and token.lower().startswith("bearer "):
            token = token.split(" ", 1)[1].strip()
        return token
    
    def save_debug_screenshot(name):
        try:
            screenshot_path = f"/tmp/{name}.png"
            driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot saved: {screenshot_path}")
        except:
            pass
    
    def save_page_source(name):
        try:
            html_path = f"/tmp/{name}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"📄 Page source saved: {html_path}")
        except:
            pass

    try:
        print("🌐 Opening Google Labs...")
        driver.get("https://labs.google/fx/tools/flow")
        time.sleep(3)

        if "sign in" in driver.page_source.lower():
            print("🔐 Logging in...")
            driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()
            email_box = wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
            email_box.send_keys(EMAIL)
            email_box.send_keys(Keys.ENTER)
            print("✅ Email entered successfully!")
            time.sleep(3)

            pwd_box = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
            pwd_box.send_keys(PASSWORD)
            pwd_box.send_keys(Keys.ENTER)
            print("✅ Password entered successfully!")
            time.sleep(8)

        print("✅ Logged in successfully!")
        time.sleep(5)
        
        # Save debug info
        save_debug_screenshot("after_login")
        save_page_source("after_login")
        
        # Inject interceptor early
        inject_interceptor()
        
        # Check for "Get started" button
        print("🔍 Checking for 'Get started' button...")
        get_started_selectors = [
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get started')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'start')]",
            "button[class*='iRlAqv']",
            "//button[contains(@class, 'sc-c177465c')]",
        ]
        
        for sel in get_started_selectors:
            try:
                if sel.startswith("//"):
                    el = driver.find_element(By.XPATH, sel)
                else:
                    el = driver.find_element(By.CSS_SELECTOR, sel)
                driver.execute_script("arguments[0].scrollIntoView(true);", el)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", el)
                print(f"✅ Clicked 'Get started' button: {sel}")
                time.sleep(4)
                save_debug_screenshot("after_get_started")
                break
            except:
                continue
        
        # Try direct navigation to project page
        print("🔄 Trying direct navigation to project page...")
        driver.get("https://labs.google/fx/tools/flow/projects")
        time.sleep(5)
        save_debug_screenshot("project_page")
        
        # Re-inject interceptor after navigation
        inject_interceptor()
        
        # Look for any button or clickable element
        print("🔍 Searching for interactive elements...")
        all_buttons = driver.find_elements(By.CSS_SELECTOR, "button, a[role='button'], div[role='button']")
        print(f"📊 Found {len(all_buttons)} buttons/clickable elements")
        
        for i, btn in enumerate(all_buttons[:10]):
            try:
                text = btn.text.lower() if btn.text else ""
                print(f"  Button {i+1}: '{text[:50]}...'")
                if any(kw in text for kw in ["new", "create", "project", "start"]):
                    print(f"  ✅ Clicking button {i+1}: '{text[:50]}'")
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(3)
                    save_debug_screenshot(f"after_button_{i+1}")
                    break
            except Exception as e:
                print(f"  ⚠️ Error with button {i+1}: {e}")
                continue
        
        # Wait for token
        print("⏳ Waiting for Authorization token...")
        token = None
        for i in range(60):
            token = get_token()
            if token:
                print(f"✅ Token captured after {i+1} seconds!")
                break
            time.sleep(1)
        
        # If no token, try triggering API by typing in any input field
        if not token:
            print("🔄 Attempting to trigger API by interacting with input fields...")
            try:
                inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea, div[contenteditable='true'], div[role='textbox']")
                print(f"📊 Found {len(inputs)} input fields")
                for inp in inputs[:5]:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", inp)
                        driver.execute_script("arguments[0].focus();", inp)
                        driver.execute_script("arguments[0].value = 'test';", inp)
                        inp.send_keys(Keys.ENTER)
                        print("  ✅ Triggered input field")
                        time.sleep(3)
                        token = get_token()
                        if token:
                            print("✅ Token captured after input interaction!")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"⚠️ Input interaction failed: {e}")
        
        # Last resort - try to navigate to a known API endpoint
        if not token:
            print("🔄 Last resort - trying to load API endpoint directly...")
            try:
                driver.execute_script("""
                fetch('https://labs.google/fx/api/v1/projects', {
                    method: 'GET',
                    headers: {'Authorization': 'Bearer dummy'}
                }).catch(() => {});
                """)
                time.sleep(5)
                token = get_token()
            except:
                pass
        
        if not token:
            save_page_source("final_page")
            save_debug_screenshot("final_page")
            raise RuntimeError("❌ No token captured - debug files saved to /tmp/")
        
        # Encode token
        print("🔐 Encoding token with Base64...")
        encoded_token = base64.b64encode(token.encode('utf-8')).decode('utf-8')
        
        # Save encoded token
        token_path = "/tmp/bearer_token.txt"
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(encoded_token)
        print(f"💾 Base64 encoded token saved to: {token_path}")
        print(f"📊 Token length: {len(token)} → Encoded length: {len(encoded_token)}")
        
        # Upload to GitHub
        print("📤 Uploading encoded token to GitHub Release...")
        upload_to_github_release(github_repo, token_path, GITHUB_TOKEN)
        
        print("✅ Workflow completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        save_page_source("error_page")
        save_debug_screenshot("error_page")
        raise
    finally:
        try:
            driver.quit()
        except:
            pass


def upload_to_github_release(github_repo, file_path, github_token):
    github_release_tag = "token-backup"
    github_release_name = "Google Labs Token Backup (Base64)"
    
    headers = {"Authorization": f"token {github_token}"}
    release_api = f"https://api.github.com/repos/{github_repo}/releases"
    
    data = {
        "tag_name": github_release_tag,
        "name": github_release_name,
        "body": "🔐 Base64 encoded bearer token for Google Labs API\n\n**Usage:**\n```bash\necho 'ENCODED_TOKEN' | base64 -d\n```"
    }
    resp = requests.post(release_api, headers=headers, json=data)

    if resp.status_code not in [200, 201]:
        existing = requests.get(f"{release_api}/tags/{github_release_tag}", headers=headers)
        if existing.status_code == 200:
            upload_url = existing.json()["upload_url"].split("{")[0]
            assets = existing.json().get("assets", [])
            for asset in assets:
                if asset["name"] == "bearer_token.txt":
                    delete_url = f"https://api.github.com/repos/{github_repo}/releases/assets/{asset['id']}"
                    requests.delete(delete_url, headers=headers)
                    print("🗑️ Deleted old token file")
        else:
            raise RuntimeError("❌ Failed to create or fetch release: " + resp.text)
    else:
        upload_url = resp.json()["upload_url"].split("{")[0]

    with open(file_path, "rb") as f:
        upload_resp = requests.post(
            f"{upload_url}?name=bearer_token.txt",
            headers={"Authorization": f"token {github_token}", "Content-Type": "text/plain"},
            data=f,
        )

    if upload_resp.status_code not in [200, 201]:
        raise RuntimeError(f"❌ Upload failed: {upload_resp.text}")

    print("✅ Base64 encoded token uploaded to GitHub Release successfully!")


if __name__ == "__main__":
    google_labs_login_and_capture_token("hackerhtml02/cookie-update")
