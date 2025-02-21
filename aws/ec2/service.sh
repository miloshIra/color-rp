cd /home/ubuntu/color-rp
git pull
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd colorai
export PYTHONUNBUFFERED=1
export DJANGO_SETTINGS_MODULE=colorai.settings
uvicorn colorai.asgi:application --host 0.0.0.0 --port 8000 --workers 4
