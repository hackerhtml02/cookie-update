from playwright.sync_api import sync_playwright
import json, os, time

EMAIL = os.getenv("GOOGLE_EMAIL")
PASSWORD = os.getenv("GOOGLE_PASSWORD")

def login_and_save_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://labs.google/fx/tools/flow")

        if "sign in" not in page.content().lower():
            print("✅ Already logged in")
        else:
            # Click Sign in
            for sel in ["text=Sign in with Google", "text=Sign in"]:
                try:
                    page.locator(sel).click(timeout=3000)
                    break
                except:
                    continue

            # Email
            page.wait_for_selector('input[type="email"]', timeout=15000)
            page.locator('input[type="email"]').fill(EMAIL)
            page.keyboard.press("Enter")
            page.wait_for_timeout(4000)

            # Password
            page.wait_for_url("**/signin/v2/sl/pwd*", timeout=15000)
            page.wait_for_selector('input[name="Passwd"]', timeout=15000)
            page.locator('input[name="Passwd"]').fill(PASSWORD)
            page.keyboard.press("Enter")
            page.wait_for_timeout(8000)

        # Save session
        context.storage_state(path="google_state.json")
        print("✅ Session saved to google_state.json")
        browser.close()
