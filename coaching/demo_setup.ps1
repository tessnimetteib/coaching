# Usage:
# 1) Open PowerShell in project root with your .venv activated
# 2) Run: .\demo-setup.ps1
#
# The script:
# - installs minimal dependencies (if requirements.txt present, uses it)
# - runs makemigrations and migrate
# - runs the demo data script via Django shell
# - (optionally) leaves the server start command commented for manual start
Set-StrictMode -Version Latest

Write-Host "1) Ensure venv is active. Proceeding..."

# If requirements.txt exists install from it, else install minimal packages
if (Test-Path "./requirements.txt") {
    Write-Host "Installing from requirements.txt..."
    python -m pip install --upgrade pip
    pip install -r requirements.txt
} else {
    Write-Host "No requirements.txt found — installing minimal packages (Django, djangorestframework)..."
    python -m pip install --upgrade pip
    pip install Django djangorestframework
}

Write-Host "2) Running makemigrations and migrate..."
python manage.py makemigrations
python manage.py migrate

Write-Host "3) Creating demo data via coaching/scripts/create_demo.py..."
# Use the shell to execute the script content
python manage.py shell -c "exec(open('coaching/scripts/create_demo.py').read())"

Write-Host "Demo data created. You can now create a superuser if needed:"
Write-Host "Run: python manage.py createsuperuser"

# Optional: start the dev server
Write-Host "To run the server now, run: python manage.py runserver"
# If you want to automatically run the server uncomment the next line:
# python manage.py runserver