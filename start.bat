@echo off
set PORT=8000

echo Running Migrations...
python manage.py migrate --noinput

echo Collecting Static Files...
python manage.py collectstatic --noinput

echo Starting Gunicorn...
gunicorn login_page.wsgi:application --bind 0.0.0.0:%PORT%
