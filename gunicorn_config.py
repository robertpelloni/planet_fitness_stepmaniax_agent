import multiprocessing

# Gunicorn configuration file for production deployment
bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
timeout = 60
accesslog = "access.log"
errorlog = "error.log"
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True
