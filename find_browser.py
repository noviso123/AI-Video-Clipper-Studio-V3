import shutil
import os

browsers = [
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "brave-browser",
    "microsoft-edge"
]

print("🔍 Searching for browsers...")
found = False
for b in browsers:
    path = shutil.which(b)
    if path:
        print(f"✅ Found {b}: {path}")
        found = True
    else:
        print(f"❌ Not found: {b}")

if not found:
    print("⚠️ No known browser found in PATH.")
