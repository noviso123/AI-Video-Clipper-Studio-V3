import sys
print("🚀 Starting Selenium Debug...", flush=True)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    print("✅ Imports successful", flush=True)

    options = Options()
    # options.add_argument("--headless=new") # Commented out to test GUI
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    print("⬇️  Installing Driver...", flush=True)
    service = Service(ChromeDriverManager().install())
    print(f"✅ Driver path: {service.path}", flush=True)

    print("🌐 Launching Chrome...", flush=True)
    driver = webdriver.Chrome(service=service, options=options)
    
    print("✅ Chrome Launched Successfully!", flush=True)
    driver.get("https://www.google.com")
    print("✅ Navigated to Google", flush=True)
    
    import time
    time.sleep(5)
    driver.quit()
    print("✅ Test Complete", flush=True)

except Exception as e:
    print(f"❌ CRITICAL ERROR: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc()
