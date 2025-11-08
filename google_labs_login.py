import os
import time
import zipfile
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def google_labs_login_and_upload(github_repo, github_release_tag="v1.0.0", github_release_name="Google Labs Profile Backup"):
    EMAIL = os.environ.get("EMAIL")
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

    try:
        print("Opening Google Labs...")
        driver.get("https://labs.google/fx/tools/flow")
        time.sleep(2)

        if "sign in" in driver.page_source.lower():
            print("Logging in...")
            driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()
            email_box = wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
            email_box.send_keys(EMAIL)
            email_box.send_keys(Keys.ENTER)
            time.sleep(3)

            pwd_box = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
            pwd_box.send_keys(PASSWORD)
            pwd_box.send_keys(Keys.ENTER)
            time.sleep(8)

        print("Logged in successfully!")

        # Close driver
        driver.quit()

        # Zip profile
        zip_path = "/tmp/chrome_profile.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(profile_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, profile_dir)
                    zipf.write(file_path, arcname)

        print("Zipped Chrome profile")

        # Upload to GitHub release
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        release_api = f"https://api.github.com/repos/{github_repo}/releases"
        data = {"tag_name": github_release_tag, "name": github_release_name}
        resp = requests.post(release_api, headers=headers, json=data)

        if resp.status_code not in [200, 201]:
            existing = requests.get(f"{release_api}/tags/{github_release_tag}", headers=headers)
            if existing.status_code == 200:
                upload_url = existing.json()["upload_url"].split("{")[0]
            else:
                raise RuntimeError("Failed to create or fetch release: " + resp.text)
        else:
            upload_url = resp.json()["upload_url"].split("{")[0]

        with open(zip_path, "rb") as f:
            upload_resp = requests.post(
                f"{upload_url}?name=chrome_profile.zip",
                headers={"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/zip"},
                data=f,
            )

        if upload_resp.status_code not in [200, 201]:
            raise RuntimeError(f"Upload failed: {upload_resp.text}")

        print("Upload completed successfully!")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    google_labs_login_and_upload("hackerhtml02/cookie-update")
