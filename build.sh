#!/bin/bash
echo "Building Vercel project..."

# Python Version
python3 -m pip install -r requirements.txt

echo "Building Tailwind CSS..."
# Navigate to the theme app and build CSS
cd theme/static_src
npm install
npm run build
cd ../..

echo "Collecting static files..."
python3 manage.py collectstatic --noinput

echo "Running migrations..."
python3 manage.py migrate
