if [ -d "venv" ]; then
  if [ -n "${VIRTUAL_ENV:-}" ] && [ "$VIRTUAL_ENV" = "$(pwd)/venv" ]; then
    deactivate 2>/dev/null || true
  fi
  rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

export FLASK_APP=app.py
export PYTHONPATH=.
export FLASK_DEBUG=1

flask run --host=0.0.0.0