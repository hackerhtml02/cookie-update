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
        
        # Check for "Get started" button and click it
        print("🔍 Checking for 'Get started' button...")
        get_started_selectors = [
            "//button[contains(., 'Get started')]",
            "button.sc-c177465c-1.iRlAqv.sc-d458a0c5-2.dzCIZN",
            "button[class*='iRlAqv']",
            "//button[text()='Get started']",
        ]
        
        get_started_clicked = False
        for sel in get_started_selectors:
            try:
                if sel.startswith("//"):
                    el = wait.until(EC.element_to_be_clickable((By.XPATH, sel)))
                else:
                    el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                el.click()
                print(f"✅ Clicked 'Get started' button: {sel}")
                get_started_clicked = True
                time.sleep(3)
                break
            except:
                continue
        
        if not get_started_clicked:
            print("ℹ️ 'Get started' button not found - proceeding to next step")
        
        # Inject interceptor
        inject_interceptor()
        
        # Click New Project button
        print("🖱️ Clicking New Project...")
        new_proj_selectors = [
            "//button[contains(., 'New project')]",
            "//div[contains(., 'New project')]",
            "button[data-testid='new-project-button']",
            "//button[contains(@class, 'new-project')]",
            "button.sc-c177465c-1",
        ]
        clicked = False
        for sel in new_proj_selectors:
            try:
                if sel.startswith("//"):
                    el = wait.until(EC.element_to_be_clickable((By.XPATH, sel)))
                else:
                    el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                el.click()
                print(f"✅ Clicked New Project: {sel}")
                clicked = True
                break
            except:
                continue
        
        if not clicked:
            print("⚠️ Warning: Could not click New Project button")
        
        time.sleep(4)
        
        # Enter prompt to trigger API requests
        print("📝 Entering prompt...")
        try:
            fields = driver.find_elements(By.CSS_SELECTOR, "textarea, input[type='text'], div[role='textbox']")
            if fields:
                fields[0].send_keys(prompt_text)
                fields[0].send_keys(Keys.ENTER)
                print("✅ Prompt submitted")
                time.sleep(2)
        except Exception as e:
            print(f"⚠️ Prompt entry failed: {e}")
        
        # Wait for token to be captured
        print("⏳ Waiting for Authorization token...")
        token = None
        for i in range(40):
            token = get_token()
            if token:
                print(f"✅ Token captured after {i+1} seconds!")
                break
            time.sleep(1)
        
        if not token:
            # Last attempt - try to find and click any interactive element to trigger API
            print("🔄 Last attempt - trying to trigger API calls...")
            try:
                clickable_elements = driver.find_elements(By.CSS_SELECTOR, "button, a, [role='button']")
                for elem in clickable_elements[:5]:
                    try:
                        elem.click()
                        time.sleep(2)
                        token = get_token()
                        if token:
                            print("✅ Token captured after clicking interactive element!")
                            break
                    except:
                        continue
            except:
                pass
        
        if not token:
            raise RuntimeError("❌ No token captured - check if profile is valid")
        
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
