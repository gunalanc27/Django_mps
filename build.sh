#!/bin/bash
# Exit on any error
set -e

echo "Building Vercel project..."

# Python Version and Pip Upgrade
echo "Upgrading pip and installing requirements..."
python3 -m pip install --upgrade pip
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
# Note: Migrations might fail during build if DB is not reachable. 
# Usually, migrations are run in a separate step or on first boot.
# But keeping it here as per previous configuration.
python3 manage.py migrate --noinput || echo "Migration skipped or failed (common during build if DB is isolated)"

echo "Build complete!"
