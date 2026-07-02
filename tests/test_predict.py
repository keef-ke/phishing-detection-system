import requests

r = requests.post("http://localhost:5000/predict", json={"url": "https://www.google.com"})
print(r.status_code)
print(r.json())