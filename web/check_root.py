import requests

for path in ['/', '/openapi.json', '/download_all', '/docs']:
    try:
        r = requests.get('http://127.0.0.1:8000' + path, timeout=5)
        print(path, r.status_code, r.headers.get('content-type'))
        text = r.text
        print(text[:400])
    except Exception as e:
        print(path, 'ERR', e)
    print('-'*40)
