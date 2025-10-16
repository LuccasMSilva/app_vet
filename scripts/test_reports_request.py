import requests

base = 'http://127.0.0.1:5000'
with requests.Session() as s:
    r = s.post(base + '/login', data={'username':'admin', 'password':'admin'})
    print('login status', r.status_code)
    r = s.get(base + '/dashboard')
    print('dashboard status', r.status_code)
    r = s.get(base + '/reports')
    print('reports status', r.status_code)
    print('\n--- REPORTS PAGE (truncated 8000 chars) ---\n')
    print(r.text[:8000])
