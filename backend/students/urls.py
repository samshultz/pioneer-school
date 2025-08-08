# students/urls.py
from rest_framework.routers import DefaultRouter
from .views import StudentProfileViewSet

router = DefaultRouter()
router.register(r"students", StudentProfileViewSet, basename="student")

urlpatterns = router.urls
