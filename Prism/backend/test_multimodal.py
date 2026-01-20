import requests
import base64
import os
import time

BASE_URL = "http://localhost:8000"

def create_dummy_image(filename="test_image.png"):
    # Create a 1x1 white pixel PNG
    # 89 50 4E 47 ...
    data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg==")
    with open(filename, "wb") as f:
        f.write(data)
    return filename

def create_dummy_audio(filename="test_audio.wav"):
    # Minimal WAV file header (44 bytes), no data
    # This might fail actual processing but passes upload validation
    header = bytes.fromhex("524946462400000057415645666d7420100000000100010044ac000088580100020010006461746100000000")
    with open(filename, "wb") as f:
        f.write(header)
    return filename

def test_api():
    print(f"Testing API at {BASE_URL}")
    
    # 1. Check Root
    try:
        r = requests.get(f"{BASE_URL}/")
        print(f"Root status: {r.status_code}")
        assert r.status_code == 200
    except Exception as e:
        print(f"Server not running? {e}")
        return

    # 2. Upload Image
    img_name = create_dummy_image()
    print(f"Uploading {img_name}...")
    with open(img_name, "rb") as f:
        files = {"file": f}
        r = requests.post(f"{BASE_URL}/api/upload", files=files)
        print(f"Upload Image: {r.status_code}, {r.json()}")
        assert r.status_code == 200
    
    # 3. List Images
    r = requests.get(f"{BASE_URL}/api/images")
    print(f"List Images: {r.status_code}, {r.json()['count']} images")
    assert r.status_code == 200
    assert any(img['file_name'] == img_name for img in r.json()['images'])

    # 4. Upload Audio
    audio_name = create_dummy_audio()
    print(f"Uploading {audio_name}...")
    with open(audio_name, "rb") as f:
        files = {"file": f}
        r = requests.post(f"{BASE_URL}/api/upload", files=files)
        print(f"Upload Audio: {r.status_code}, {r.json()}")
        assert r.status_code == 200

    # 5. List Audio
    r = requests.get(f"{BASE_URL}/api/audio")
    print(f"List Audio: {r.status_code}, {r.json()['audio']}")
    assert r.status_code == 200
    assert any(audio['file_name'] == audio_name for audio in r.json()['audio'])

    # Cleanup
    try:
        os.remove(img_name)
        os.remove(audio_name)
    except:
        pass
    
    print("✅ Basic API verification passed!")

if __name__ == "__main__":
    test_api()
