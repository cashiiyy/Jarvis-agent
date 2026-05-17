import os
import urllib.request
import ssl

def download_file(url, destination):
    print(f"Downloading {url} to {destination}...")
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(url, context=context) as response, open(destination, 'wb') as out_file:
        data = response.read()
        out_file.write(data)
    print("Done.")

def main():
    base_path = r"K:\PROJECTS\Phone agent\venv\Lib\site-packages\openwakeword\resources\models"
    
    # Missing model reported in error
    models_to_download = [
        ("https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/embedding_model.onnx", "embedding_model.onnx"),
    ]
    
    if not os.path.exists(base_path):
        print(f"Error: Path {base_path} does not exist. Are you sure the venv is at K:\\PROJECTS\\Phone agent\\venv?")
        return

    for url, filename in models_to_download:
        dest = os.path.join(base_path, filename)
        if not os.path.exists(dest):
            try:
                download_file(url, dest)
            except Exception as e:
                print(f"Failed to download {filename}: {e}")
        else:
            print(f"{filename} already exists.")

if __name__ == "__main__":
    main()
