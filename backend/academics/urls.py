from rest_framework.routers import DefaultRouter
from .views import (
    ClassViewSet, 
    SubjectViewSet, 
    ClassSubjectViewSet, 
    TimetableViewSet
)

router = DefaultRouter()
router.register("classes", ClassViewSet, basename="class")
router.register("subjects", SubjectViewSet, basename="subject")
router.register("class-subjects", ClassSubjectViewSet, basename="class-subject")
router.register(r'timetables', TimetableViewSet, basename='timetable')
urlpatterns = router.urls
