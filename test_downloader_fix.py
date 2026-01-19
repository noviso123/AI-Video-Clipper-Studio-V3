from src.modules.downloader import VideoDownloader
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_download():
    print("🚀 Testing Downloader with Android Client Fix...")
    dl = VideoDownloader()
    try:
        # A guaranteed public long-form video (Rick Astley - Never Gonna Give You Up)
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 
        result = dl.download_video(url)
        print("✅ Download SUCCESS!")
        print(f"Video: {result['video_path']}")
        
        # Cleanup
        dl.cleanup(result['metadata']['video_id'])
        
    except Exception as e:
        print(f"❌ Download FAILED: {e}")

if __name__ == "__main__":
    test_download()
