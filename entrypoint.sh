#!/bin/sh

# Run Alembic Upgrade to apply migrations
alembic upgrade head

# Then start your Python application
exec python main.py
