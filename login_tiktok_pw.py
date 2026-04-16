from playwright.sync_api import sync_playwright
import os

PROFILE_PATH = r"C:\Users\ASUS\pw_profile_tiktok"

if not os.path.exists(PROFILE_PATH):
    os.makedirs(PROFILE_PATH)

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_PATH,
        headless=False
    )

    page = browser.new_page()
    page.goto("https://www.tiktok.com")

    print("🔐 LOGIN TIKTOK DI BROWSER INI")
    print("✅ Setelah login BERHASIL, tekan ENTER di terminal")
    input()

    browser.close()
    print("✅ Login Playwright tersimpan")
