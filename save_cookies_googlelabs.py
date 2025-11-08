# save_cookies_googlelabs.py
import os, time, json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# Put your email here
EMAIL = "muhammadharis8765@imagescraftai.live"   # <-- replace

def get_password_from_env():
    p = os.environ.get("PASSWORD")
    if not p:
        raise SystemExit("PASSWORD env var required")
    return p

class GoogleLabsLogin:
    def __init__(self, email, password):
        self.email = email
        self.password = password
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
        options.add_argument("--headless=new")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Selenium 4.25+ uses Selenium Manager automatically
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)

    def click_sign_in_button(self):
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
                time.sleep(1)
                try:
                    btn.click()
                except:
                    self.driver.execute_script("arguments[0].click();", btn)
                return True
            except Exception:
                continue
        return False

    def login(self):
        self.driver.get("https://labs.google/fx/tools/flow")
        time.sleep(2)
        if "sign in" not in self.driver.page_source.lower():
            return True
        if not self.click_sign_in_button():
            return False
        try:
            email_input = self.wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
            email_input.send_keys(self.email)
            email_input.send_keys(Keys.ENTER)
            time.sleep(3)
            passwd_input = self.wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
            passwd_input.send_keys(self.password)
            passwd_input.send_keys(Keys.ENTER)
            time.sleep(8)
            return True
        except TimeoutException:
            return False

    def save_cookies_json(self, filename="cookies.json"):
        cookies = self.driver.get_cookies()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    PASSWORD = get_password_from_env()
    bot = GoogleLabsLogin(EMAIL, PASSWORD)
    try:
        if bot.login():
            bot.save_cookies_json("cookies.json")
    finally:
        bot.close()
