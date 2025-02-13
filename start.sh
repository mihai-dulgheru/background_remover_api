#!/usr/bin/env bash

gunicorn app:app --bind 127.0.0.1:8000 --workers 3 --timeout 120 &
nginx -g "daemon off;"
