import requests

try:
    r = requests.get('http://127.0.0.1:8000/download_all', timeout=10)
    print('status:', r.status_code)
    print('content-type:', r.headers.get('content-type'))
    print('content-length:', len(r.content))
    print('first-bytes:', repr(r.content[:120]))
    if r.status_code != 200:
        print('text:', r.text[:400])
except Exception as e:
    print('error:', e)
