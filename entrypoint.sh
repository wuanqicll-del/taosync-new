#!/bin/bash
set -e
cd /app
if [ ! -f front/index.html ]; then
    echo "Building frontend..."
    cd frontend && npm install && npm run build && cd ..
    cp -r frontend/dist/* front/
    echo "Frontend built."
fi
cd /app
exec python main.py
