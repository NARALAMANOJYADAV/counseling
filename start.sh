set -e
echo "--- SERVER STARTING ---"

echo "RUNNING MIGRATIONS..."
python manage.py migrate --no-input

echo "CHECKING ADMIN USERS..."
python create_admin.py || echo "Admin check done"
python create_approval_users.py || echo "Approval users check done"

echo "STARTING GUNICORN ON PORT 8000..."
# Pinning port to 8000 for consistency; Render will map this to the public URL.
INTERNAL_PORT=${PORT:-8000}
exec gunicorn student.wsgi:application --bind 0.0.0.0:$INTERNAL_PORT --timeout 120 --workers 1 --log-level info
