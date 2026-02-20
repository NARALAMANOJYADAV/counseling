set -e
echo "--- SERVER STARTING ---"

echo "RUNNING MIGRATIONS..."
python manage.py migrate --no-input

echo "CHECKING ADMIN USERS..."
python create_admin.py || echo "Admin check done"
python create_approval_users.py || echo "Approval users check done"

echo "STARTING GUNICORN..."
exec gunicorn student.wsgi:application --bind 0.0.0.0:${PORT:-8000} --timeout 120 --workers 1 --log-level info
