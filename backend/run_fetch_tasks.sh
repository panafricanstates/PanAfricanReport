#!/bin/bash
# Run all news fetches synchronously without Docker/Celery.

set -e

if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Please create it first."
    exit 1
fi

echo "Running fetch tasks..."
python manual_tasks.py

deactivate
echo "Done."
