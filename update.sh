#!/bin/bash
cd /opt/aivm-photo-api
git pull origin main
/opt/aivm-photo-api/venv/bin/pip install -r requirements.txt
sudo systemctl restart aivm-api.service