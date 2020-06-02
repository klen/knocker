#!/bin/bash
set -e

env

if [ "$1" = 'knocker' ]; then
    echo -e "\nDocker: Start Knocker"
    exec uvicorn --host=0.0.0.0 knocker:app
fi

echo ""
exec "$@"
