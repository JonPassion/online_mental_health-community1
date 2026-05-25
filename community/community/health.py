import time
from django.http import JsonResponse
from django.db import connection
from django.db.utils import OperationalError


def health_check(request):
    """
    Lightweight health-check endpoint used by Render (and any uptime monitor).

    Returns HTTP 200 with a JSON payload when the app and database are healthy.
    Returns HTTP 503 when the database is unreachable.

    GET /health/
    """
    start = time.monotonic()

    db_ok = True
    db_error = None
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except OperationalError as exc:
        db_ok = False
        db_error = str(exc)

    elapsed_ms = round((time.monotonic() - start) * 1000, 2)

    payload = {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else f"error: {db_error}",
        "response_ms": elapsed_ms,
    }

    status_code = 200 if db_ok else 503
    return JsonResponse(payload, status=status_code)
