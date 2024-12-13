Git clone project

!cd app

pip install -r requirement.txt

Run app: uvicorn main:app --reload --host 0.0.0.0 --port 8069

Test api by making simple python code to make request

import requests

# URL of the API endpoint
url = "http://localhost:8069/ocr/"
file_path = ""
# Open the file you want to send in the request
with open(file_path, "rb") as file:
    # Prepare the file to send in the request
    files = {"file": ("test.pdf", file, "application/pdf")}

    # Send the POST request with the file
    response = requests.post(url, files=files, stream=True)

    # Ensure the response is successful
    if response.status_code == 200:
        # Iterate through the response stream
        for line in response.iter_lines():
            if line:
                # Decode the line and strip any unnecessary spaces or newline characters
                decoded_line = line.decode("utf-8").strip()

                # If data is received, print it
                if decoded_line:
                    print(decoded_line)

    else:
        print(f"Error: {response.status_code}")
