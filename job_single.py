import schedule
import time
import requests
from entities.FinalReview import FinalReview

URL = '200.239.129.7'
# URL = 'localhost'

def job(uid):
    resp = requests.get(f'http://{URL}:5000/comparators-robot/{uid}')
    print( resp )
    time.sleep(2)
    resp = requests.get(f'http://{URL}:5000/comparators-robot-job/{uid}')
    print( resp )
    time.sleep(2)
    resp = requests.get(f'http://{URL}:5000/systematic_review/i2/{uid}')
    print( resp )
    time.sleep(2)
    resp = requests.get(f'http://{URL}:5000/comparators-calc/{uid}')
    print( resp )
    time.sleep(2)


# schedule.every(10).seconds.do(job)

# while True:
#     schedule.run_pending()
#     time.sleep(1)

# job('0d03a4e2-7f68-42df-987a-8f196a5e0cfd')
job('935f6761-fc97-43c4-938b-40e28c18ca8e')