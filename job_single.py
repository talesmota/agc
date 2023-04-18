import time
import requests

# URL = '200.239.129.7'
URL = 'localhost'

def job(uid):
    resp = requests.get(f'http://{URL}:5000/comparators-robot/{uid}')
    print( resp.text )
    time.sleep(2)
    resp = requests.get(f'http://{URL}:5000/comparators-robot-job/{uid}')
    print( resp.text )
    time.sleep(2)
    resp = requests.get(f'http://{URL}:5000/systematic_review/i2/{uid}')
    print( resp.text )
    time.sleep(2)
    resp = requests.get(f'http://{URL}:5000/comparators-calc/{uid}')
    print( resp.text )
    time.sleep(2)

job('0d03a4e2-7f68-42df-987a-8f196a5e0cfd')