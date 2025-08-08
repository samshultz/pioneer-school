from django.http import JsonResponse
from django.db import connection
import redis
from django.conf import settings

def health_check(request):
    status = {"status": "ok"}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        status["database"] = "ok"
    except Exception as e:
        status["database"] = f"error: {str(e)}"
        status["status"] = "unhealthy"

    # --- Check Redis ---
    try:
        r = redis.StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            socket_connect_timeout=2,
        )
        r.ping()
        status["redis"] = "ok"
    except Exception as e:
        status["redis"] = f"error: {str(e)}"
        status["status"] = "unhealthy"

    return JsonResponse(status, status=200 if status["status"] == "ok" else 500)