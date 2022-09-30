#!/bin/sh
echo "Generating users..."
python3 fake_user.py
echo

echo "Generating activities..."
python3 fake_activities.py
echo

echo "Data generation complete."
