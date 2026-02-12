import requests
r = requests.get('http://127.0.0.1:8000/openapi.json', timeout=5)
js = r.text
print('/download_all' in js)
print(js[:2000])
