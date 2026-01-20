import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
try:
    import whisper
    print("✅ Whisper imported successfully")
except ImportError as e:
    print(f"❌ Failed to import whisper: {e}")
    import pkg_resources
    try:
        dist = pkg_resources.get_distribution('openai-whisper')
        print(f"openai-whisper version: {dist.version}")
        print(f"Location: {dist.location}")
    except:
        print("openai-whisper not found in pkg_resources")
