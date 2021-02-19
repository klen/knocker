#!/bin/bash
set -e

env

if [ "$1" = 'knocker' ]; then
    echo -e "\nDocker: Start Knocker"
    exec gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --access-logfile - knocker.app:app
fi

echo ""
exec "$@"
