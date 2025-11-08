from playwright.sync_api import sync_playwright
import json, os, time

EMAIL = os.getenv("GOOGLE_EMAIL")
PASSWORD = os.getenv("GOOGLE_PASSWORD")
COOKIE_PATH = "cookies.json"

def login_and_save_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://labs.google/fx/tools/flow")

        # Check if already logged in
        if "sign in" not in page.content().lower():
            print("✅ Already logged in")
        else:
            # Click sign in
            btns = ["text=Sign in with Google", "text=Sign in"]
            for sel in btns:
                try:
                    page.locator(sel).click(timeout=3000)
                    break
                except:
                    continue

            # Enter credentials
            page.locator('input[type="email"]').fill(EMAIL)
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
            page.locator('input[type="password"]').fill(PASSWORD)
            page.keyboard.press("Enter")
            page.wait_for_timeout(8000)

        # Save cookies
        cookies = context.cookies()
        with open(COOKIE_PATH, "w") as f:
            json.dump(cookies, f)
        print("✅ Cookies saved to", COOKIE_PATH)

        browser.close()

if __name__ == "__main__":
    login_and_save_cookies()
