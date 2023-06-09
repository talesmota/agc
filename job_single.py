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

job('b658c63f-056e-4664-80d6-7046c118e58f')