from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://www.tiktok.com")

    print("👉 SILAKAN LOGIN TIKTOK DI BROWSER")
    print("👉 SETELAH LOGIN BERHASIL, KEMBALI KE TERMINAL DAN TEKAN ENTER")
    input()

    context.storage_state(path="tiktok_state.json")
    browser.close()

    print("✅ Login berhasil disimpan ke tiktok_state.json")
