import requests, uuid
B='http://127.0.0.1:8000/api'
def ok(r): assert r.status_code < 400, r.text
ok(requests.get(B+'/health')); ok(requests.post(B+'/seed'))
e=f't_{uuid.uuid4().hex[:8]}@example.com'
r=requests.post(B+'/auth/register',json={'name':'Smoke Student','email':e,'password':'pass1234','role':'Student'}); ok(r)
r=requests.post(B+'/auth/login',json={'email':e,'password':'pass1234'}); ok(r)
h={'Authorization':'Bearer '+r.json()['access_token']}
ok(requests.put(B+'/skill-profiles',headers=h,json={'technical_score':80,'soft_score':75,'skills':['Python','Pandas'],'strengths':['Python'],'gaps':['ML'],'interests':['AI']}))
ok(requests.get(B+'/recommendations',headers=h))
print('Smoke test passed')
