#!/bin/sh

# For macOS: https://stackoverflow.com/a/52230415/78903
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
export FLASK_ENV=production
export FLASK_RUN_HOST="${FLASK_RUN_HOST:=0.0.0.0}"
export FLASK_RUN_PORT="${FLASK_RUN_PORT:=5000}"
export REDIS_URL="redis://redis:6379/0"
flask run
