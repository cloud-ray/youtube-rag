# gunicorn_config.py
bind = "0.0.0.0:8080"
workers = 2  # Reduce the number of workers
timeout = 120
accesslog = '-'  # '-' means log to stdout
errorlog = '-'   # '-' means log to stderr
loglevel = 'info'
