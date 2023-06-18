import time
import requests

# URL = '200.239.129.7'
URL = 'localhost'


def job(uid):
    resp = requests.get(f'http://{URL}:5000/comparators-robot/{uid}')
    print(resp.text)
    time.sleep(2)
    resp = requests.get(f'http://{URL}:5000/comparators-robot-job/{uid}')
    print(resp.text)
    time.sleep(2)
    resp = requests.get(f'http://{URL}:5000/systematic_review/i2/{uid}')
    print(resp.text)
    time.sleep(2)
    resp = requests.get(f'http://{URL}:5000/comparators-calc/{uid}')
    print(resp.text)
    time.sleep(2)


job('52d25e08-fe1f-4e6f-97fa-9f4ab72f97c8')
