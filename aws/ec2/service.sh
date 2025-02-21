cd /home/ubuntu/color-rp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 colorai/manage.py runserver 0.0.0.0:8000 --noreload
