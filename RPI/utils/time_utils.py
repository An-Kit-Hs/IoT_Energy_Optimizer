import time
import datetime

def now():
    return time.time()

def seconds_since(ts):
    return time.time() - ts

def current_hour():
    return datetime.datetime.now().hour

def minutes_since(ts):
    return (time.time() - ts) / 60