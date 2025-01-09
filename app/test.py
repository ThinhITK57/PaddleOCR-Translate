import requests
url="http://localhost:8069/ocr/"
file_path = "test_bug.pdf"
with open(file_path, "rb") as file:
    # Prepare the file to send in the request
    files = {"file": ("test.pdf", file, "application/pdf")}
    # Send the POST request with the file
    params = {"lang": "en"}
    response = requests.post(url, files=files, params=params, stream=True)
    print(response)
    # Ensure the response is successful
    # if response.status_code == 200:
    #     # Iterate through the response stream
    #     for line in response.iter_lines():
    #         if line:
    #             # Decode the line and strip any unnecessary spaces or newline characters
    #             decoded_line = line.decode("utf-8").strip()
    #             # If data is received, print it
    #             if decoded_line:
    #                 print(decoded_line)
    # else:
    #     print(f"Error: {response.status_code}")