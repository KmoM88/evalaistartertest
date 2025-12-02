import requests
import time
import json

URL = "https://staging.eval.ai/api/jobs/challenge/882/challenge_phase/2348/submission/"
TOKEN = "YOUR_API_TOKEN"
FILE_PATH = "challenge.txt"
headers = {
    "Authorization": f"Token {TOKEN}",
}

submission_metadata = [
    {
        "name": "TextAttribute",
        "type": "text",
        "required": False,
        "description": "Sample",
        "value": None
    },
    {
        "name": "SingleOptionAttribute",
        "type": "radio",
        "options": ["A", "B", "C"],
        "description": "Sample",
        "value": None
    },
    {
        "name": "MultipleChoiceAttribute",
        "type": "checkbox",
        "options": ["alpha", "beta", "gamma"],
        "description": "Sample",
        "values": []
    },
    {
        "name": "TrueFalseField",
        "type": "boolean",
        "required": False,
        "description": "Sample",
        "value": None
    }
]

for i in range(5):
    print(f"Enviando submission #{i}")

    files = {
        "input_file": open(FILE_PATH, "rb"),
    }

    data = {
        "status": "submitting",
        "method_name": "",
        "method_description": "",
        "project_url": "",
        "publication_url": "",
        "submission_metadata": json.dumps(submission_metadata),
    }

    response = requests.post(URL, headers=headers, files=files, data=data)

    print("Status:", response.status_code)
    try:
        print("Response:", response.json())
    except:
        print("Response text:", response.text)

    files["input_file"].close()
    time.sleep(1)
