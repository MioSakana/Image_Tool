import requests, time, os
url = 'http://127.0.0.1:8000/process_async'
with open('imgs/main.png','rb') as imgf:
    for action in ['sharpen','bleach','orientation']:
        print('Testing action', action)
        files = {'file': imgf}
        r = requests.post(url, files=files, data={'action':action})
        imgf.seek(0)
        if r.status_code != 200:
            print('Failed to enqueue:', r.status_code, r.text)
            continue
        js = r.json()
        job_id = js['job_id']
        print('job_id', job_id)
        status_url = f"http://127.0.0.1:8000/status/{job_id}"
        result_url = f"http://127.0.0.1:8000/result/{job_id}"
        for _ in range(60):
            s = requests.get(status_url)
            print('status:', s.text)
            if 'finished' in s.text:
                r2 = requests.get(result_url)
                if r2.status_code==200:
                    outp = os.path.join('web','results', f'{job_id}_{action}.jpg')
                    with open(outp,'wb') as f:
                        f.write(r2.content)
                    print('Saved', outp)
                break
            time.sleep(1)
print('Done')
