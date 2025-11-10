import time

import redis
from flask import Flask
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
cache = redis.Redis(host='redis', port=6379)

# Prometheus metrics
REQUEST_COUNT = Counter('flask_app_request_count', 'Total request count', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('flask_app_request_latency_seconds', 'Request latency', ['endpoint'])
HITS_COUNTER = Counter('flask_app_hits_total', 'Total number of hits')

def get_hit_count():
    retries = 5
    while True:
        try:
            return cache.incr('hits')
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)

@app.route('/')
def hello():
    start_time = time.time()
    count = get_hit_count()
    HITS_COUNTER.inc()

    status = 200
    REQUEST_COUNT.labels(method='GET', endpoint='/', status=status).inc()
    REQUEST_LATENCY.labels(endpoint='/').observe(time.time() - start_time)

    return f'Hello World! I have been seen {count} times.\n', status

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}