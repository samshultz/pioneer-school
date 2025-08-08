from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from health.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path("api/", include("students.urls")),
    path("api/", include("teachers.urls")),
    path("api/", include("students.urls")),
    path("api/academics/", include("academics.urls")),
    path("api/attendance/", include("attendance.urls")),
    path("health/", health_check),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
