# Procfile at repo root (used by the API app)
release: bash -lc 'if [ "$RUN_MIGRATIONS" = "true" ]; then alembic upgrade head; else echo "Skipping migrations (RUN_MIGRATIONS!=true)"; fi'
web: gunicorn api.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
