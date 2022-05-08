#!/bin/bash
# taken from https://www.phusionpassenger.com/library/deploy/nginx/automating_app_updates/python/

set -e

APP_DIR=/home/danial/attacker-controller/
RESTART_ARGS=


### Automation steps ###

set -x

cd $APP_DIR/
git pull

# Activate the virtualenv and install the dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Restart the app
passenger-config restart-app --ignore-app-not-running --ignore-passenger-not-running "$RESTART_ARGS" $APP_DIR/code