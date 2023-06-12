#!/bin/bash

if [ "$1" == "start" ]; then
    flask db upgrade
    gunicorn --bind 0.0.0.0:5000 --timeout 600 wsgi:app
elif [ "$1" == "shell" ]; then
    /bin/bash
else
    echo "Unknown command: $1"
    exit 1
fi
