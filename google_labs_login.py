#!/usr/bin/env python3
import os
import time
import base64
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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
            window.__capturedCookies = document.cookie;
            
            const origFetch = window.fetch.bind(window);
            window.fetch = function() {
                const args = Array.from(arguments);
                const opts = args[1] || {};
                if (opts.headers) {
                    for (let k in opts.headers) {
                        if (k.toLowerCase() === 'authorization') {
                            window.__capturedAuthToken = opts.headers[k];
                            console.log('✅ Token captured via fetch:', opts.headers[k].substring(0, 50) + '...');
                        }
                    }
                }
                return origFetch.apply(this, args);
            };
            
            const origXHR = XMLHttpRequest.prototype.setRequestHeader;
            XMLHttpRequest.prototype.setRequestHeader = function(header, value) {
                if (header.toLowerCase() === 'authorization') {
                    window.__capturedAuthToken = value;
                    console.log('✅ Token captured via XHR:', value.substring(0, 50) + '...');
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

    def wait_for_page_load():
        """Wait for page to be fully loaded"""
        driver.execute_script("return document.readyState") == "complete"
        time.sleep(2)

    try:
        print("🌐 Opening Google Labs...")
        driver.get("https://labs.google/fx/tools/flow")
        wait_for_page_load()

        if "sign in" in driver.page_source.lower():
            print("🔐 Logging in...")
            try:
                sign_in_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Sign in')]")))
                sign_in_btn.click()
            except:
                # Try alternative selectors
                driver.find_element(By.XPATH, "//*[contains(text(), 'Sign in')]").click()
            
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
        wait_for_page_load()
        
        # Inject interceptor early
        inject_interceptor()
        time.sleep(2)
        
        # Try multiple strategies to trigger API calls
        print("🔄 Attempting to trigger API calls...")
        
        # Strategy 1: Look for existing project or create new
        try:
            print("📂 Checking for existing projects...")
            # Wait for the main content to load
            time.sleep(5)
            
            # Try to find and click any interactive element
            interactive_elements = [
                "//button",
                "//a[contains(@href, 'project')]",
                "//div[@role='button']",
                "[data-testid*='project']",
                "[data-testid*='new']",
            ]
            
            for selector in interactive_elements:
                try:
                    if selector.startswith("//"):
                        elements = driver.find_elements(By.XPATH, selector)
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        print(f"🖱️ Found {len(elements)} elements with selector: {selector}")
                        for elem in elements[:3]:  # Try first 3 elements
                            try:
                                elem.click()
                                print(f"✅ Clicked element: {elem.text[:50] if elem.text else 'No text'}")
                                time.sleep(2)
                                inject_interceptor()  # Re-inject after page change
                                break
                            except:
                                continue
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"⚠️ Strategy 1 failed: {e}")
        
        # Strategy 2: Navigate directly to a project URL
        try:
            print("🌐 Trying direct project navigation...")
            driver.get("https://labs.google/fx/tools/flow/project")
            wait_for_page_load()
            inject_interceptor()
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ Strategy 2 failed: {e}")
        
        # Strategy 3: Try to interact with any input field
        try:
            print("📝 Looking for input fields...")
            input_selectors = [
                "textarea",
                "input[type='text']",
                "div[role='textbox']",
                "[contenteditable='true']",
            ]
            
            for selector in input_selectors:
                try:
                    fields = driver.find_elements(By.CSS_SELECTOR, selector)
                    if fields:
                        print(f"✅ Found {len(fields)} input fields")
                        fields[0].click()
                        time.sleep(1)
                        fields[0].send_keys(prompt_text)
                        time.sleep(1)
                        fields[0].send_keys(Keys.ENTER)
                        print("✅ Prompt submitted")
                        time.sleep(3)
                        break
                except:
                    continue
        except Exception as e:
            print(f"⚠️ Strategy 3 failed: {e}")
        
        # Strategy 4: Refresh and check for token in cookies/storage
        print("🔄 Refreshing page to trigger authentication...")
        driver.refresh()
        wait_for_page_load()
        inject_interceptor()
        time.sleep(5)
        
        # Wait for token to be captured
        print("⏳ Waiting for Authorization token...")
        token = None
        for i in range(60):  # Increased wait time
            token = get_token()
            if token:
                print(f"✅ Token captured after {i+1} seconds!")
                break
            
            # Log console for debugging
            if i % 10 == 0:
                logs = driver.get_log('browser')
                if logs:
                    print(f"📋 Browser console ({len(logs)} messages):")
                    for log in logs[-5:]:  # Last 5 messages
                        print(f"  {log['message'][:100]}")
            
            time.sleep(1)
        
        # Fallback: Try to extract token from browser storage
        if not token:
            print("⚠️ Trying fallback: extracting from storage...")
            storage_token = driver.execute_script("""
                return localStorage.getItem('authToken') || 
                       sessionStorage.getItem('authToken') ||
                       localStorage.getItem('token') ||
                       sessionStorage.getItem('token');
            """)
            if storage_token:
                token = storage_token
                print("✅ Token found in browser storage!")
        
        if not token:
            # Save page source for debugging
            with open("/tmp/page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("💾 Page source saved to /tmp/page_source.html")
            
            # Take screenshot
            driver.save_screenshot("/tmp/screenshot.png")
            print("📸 Screenshot saved to /tmp/screenshot.png")
            
            raise RuntimeError("❌ No token captured after all strategies - check artifacts for debugging")
        
        # Encode token in Base64
        print("🔐 Encoding token with Base64...")
        encoded_token = base64.b64encode(token.encode('utf-8')).decode('utf-8')
        
        # Save encoded token to file
        token_path = "/tmp/bearer_token.txt"
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(encoded_token)
        print(f"💾 Base64 encoded token saved to: {token_path}")
        print(f"📊 Token length: {len(token)} → Encoded length: {len(encoded_token)}")
        
        # Upload token to GitHub Release
        print("📤 Uploading encoded token to GitHub Release...")
        upload_to_github_release(github_repo, token_path, GITHUB_TOKEN)
        
        print("✅ Workflow completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
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
    
    # Try to create release
    data = {
        "tag_name": github_release_tag,
        "name": github_release_name,
        "body": "🔐 Base64 encoded bearer token for Google Labs API\n\n**Usage:**\n```bash\necho 'ENCODED_TOKEN' | base64 -d\n```"
    }
    resp = requests.post(release_api, headers=headers, json=data)

    if resp.status_code not in [200, 201]:
        # Release might already exist, fetch it
        existing = requests.get(f"{release_api}/tags/{github_release_tag}", headers=headers)
        if existing.status_code == 200:
            release_id = existing.json()["id"]
            upload_url = existing.json()["upload_url"].split("{")[0]
            
            # Delete old assets
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

    # Upload token file
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
