import os
import json


SCHEMA = 'https'
MAX_REDIRECTS = 10
STATUS_URL = '/knocker/status'

#  Timeout
#  -------

TIMEOUT = 10.0
TIMEOUT_MAX = 60.0

#  Retries
#  -------

RETRIES = 2
RETRIES_MAX = 10

RETRIES_BACKOFF_FACTOR = 0.5
RETRIES_BACKOFF_FACTOR_MAX = 60


# Process ENVIRONMENT
# -------------------

scope = locals()
for name in os.environ:
    if not (name in scope and name.upper() == name):
        continue

    try:
        scope[name] = json.loads(os.environ[name])
    except ValueError:
        pass
