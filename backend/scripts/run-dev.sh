set -e
set -x

exec python3 -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:5678 \
    -m uvicorn app.main:app --host 0.0.0.0 --reload