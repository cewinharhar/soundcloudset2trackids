import os
import json
from dotenv import load_dotenv
from acrcloud.recognizer import ACRCloudRecognizer

load_dotenv()


def recognize_with_acr(file_path: str):
    try:
        acr = ACRCloudRecognizer({
            "host": os.getenv("ACR_HOST"),
            "access_key": os.getenv("ACR_KEY"),
            "access_secret": os.getenv("ACR_SECRET"),
            "timeout": 10
        })
        result = acr.recognize_by_file(file_path, 0)
        data = json.loads(result)
        metadata = data.get("metadata", {}).get("music", [])
        if metadata:
            top = metadata[0]
            return {"title": top.get("title"), "artist": top.get("artists", [{}])[0].get("name")}
        else:
            print(f"No track found for {file_path}. Full response: {data}")
            return "not found"
    except Exception as e:
        print(f"Error recognizing {file_path}: {e}")
        return {"error": str(e), "file": file_path}

