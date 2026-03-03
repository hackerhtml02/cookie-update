from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import json, os, time

EMAIL = "newtk1@latterlavender.cfd"
PASSWORD = "Haris123@"
STATE_FILE = "google_state.json"

def login_and_save_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--start-maximized"]
        )

        context = browser.new_context(
            viewport={"width": 1280, "height": 800}
        )

        page = context.new_page()

        print("🌍 Opening Adobe account page...")
        page.goto("https://account.adobe.com/", timeout=60000)
        page.wait_for_load_state("networkidle")

        try:
            # Direct Google Button Click
            print("🔎 Waiting for Google Sign-In button...")
            page.wait_for_selector(
                'button[data-id="EmailPage-GoogleSignInButton"]',
                timeout=20000
            )

            print("🖱 Clicking Continue with Google...")
            page.locator(
                'button[data-id="EmailPage-GoogleSignInButton"]'
            ).click()

        except PlaywrightTimeoutError:
            print("❌ Google button not found!")
            browser.close()
            return

        # Wait for Google login page
        try:
            print("📧 Waiting for Email field...")
            page.wait_for_selector('input[type="email"]', timeout=30000)
            time.sleep(3)

            page.fill('input[type="email"]', EMAIL)
            page.keyboard.press("Enter")

        except PlaywrightTimeoutError:
            print("❌ Email field not found!")
            browser.close()
            return

        # Password
        try:
            print("🔐 Waiting for Password field...")
            page.wait_for_selector('input[type="password"]', timeout=30000)
            time.sleep(3)

            page.fill('input[type="password"]', PASSWORD)
            page.keyboard.press("Enter")

        except PlaywrightTimeoutError:
            print("❌ Password field not found!")
            browser.close()
            return

        # Final wait after login
        print("⏳ Waiting for login to complete...")
        page.wait_for_load_state("networkidle")
        time.sleep(8)

        # Save session
        context.storage_state(path=STATE_FILE)
        print(f"✅ Session saved to {STATE_FILE}")

        browser.close()


if __name__ == "__main__":
    login_and_save_cookies()
