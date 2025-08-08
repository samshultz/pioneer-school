from rest_framework import serializers
from users.models import Membership
from .models import (
    Class, 
    Subject, 
    ClassSubject,
    Timetable
)


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ["id", "name", "section", "created_at"]


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "code", "created_at"]


class ClassSubjectSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.get_full_name", read_only=True)
    teacher_email = serializers.EmailField(source="teacher.user.email", read_only=True)

    class Meta:
        model = ClassSubject
        fields = [
            "id", 
            "school_class", 
            "subject", 
            "teacher", 
            "teacher_name", 
            "teacher_email"
        ]


class TimetableSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(
        source="class_subject.subject.name",
        read_only=True
    )
    class_name = serializers.CharField(
        source="class_subject.school_class.name",
        read_only=True
    )
    teacher_name = serializers.SerializerMethodField()

    # teacher_name = serializers.CharField(
    #     source="class_subject.teacher.membership.user.get_full_name",
    #     read_only=True
    # )

    class Meta:
        model = Timetable
        fields = [
            "id",
            "class_subject",
            "day_of_week",
            "start_time",
            "end_time",
            "room",
            "subject_name",
            "class_name",
            "teacher_name",
        ]
        read_only_fields = ["id", "created_at"]

    def get_teacher_name(self, obj):
        if obj.class_subject and obj.class_subject.teacher:
            return obj.class_subject.teacher.membership.user.get_full_name()
        return None
    
    def get_subject_name(self, obj):
        return obj.class_subject.subject.name if obj.class_subject else None

    def get_class_name(self, obj):
        return obj.class_subject.school_class.name if obj.class_subject else None

    def validate(self, attrs):
        class_subject = attrs.get("class_subject") or getattr(self.instance, "class_subject", None)
        day_of_week = attrs.get("day_of_week") or getattr(self.instance, "day_of_week", None)
        start_time = attrs.get("start_time") or getattr(self.instance, "start_time", None)
        end_time = attrs.get("end_time") or getattr(self.instance, "end_time", None)
        room = attrs.get("room") or getattr(self.instance, "room", None)

        print("🔍 Validating timetable:")
        print(f"   Class: {class_subject.school_class}")
        print(f"   Teacher: {class_subject.teacher}")
        print(f"   Day: {day_of_week}, Time: {start_time} - {end_time}, Room: {room}")

        # ⏱️ Time validity
        if start_time and end_time and start_time >= end_time:
            print("❌ Invalid: Start time is after or equal to end time")
            raise serializers.ValidationError({
                "non_field_errors": ["Start time must be before end time."]
            })

        # Base queryset for overlap check
        qs = Timetable.objects.filter(
            day_of_week=day_of_week,
            start_time__lt=end_time,
            end_time__gt=start_time,
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        print(f"   Overlap candidates: {qs.count()}")

        errors = []

        # 👨‍🏫 Teacher conflict
        if qs.filter(class_subject__teacher=class_subject.teacher).exists():
            print("❌ Conflict: Teacher is already assigned")
            # raise serializers.ValidationError({
                # "non_field_errors": ["Teacher is already assigned during this time."]
            # })
            errors.append("Teacher is already assigned during this time.")
        
        # 🏫 Class conflict
        if qs.filter(class_subject__school_class=class_subject.school_class).exists():
            print("❌ Conflict: Class already has a timetable")
            errors.append("Class already has a timetable during this time.")
            # raise serializers.ValidationError({
            #     "non_field_errors": ["Class already has a timetable during this time."]
            # })


        # 🚪 Room conflict
        if room and qs.filter(room=room).exists():
            print(f"❌ Conflict: Room {room} is already occupied")
            errors.append(f"Room '{room}' is already occupied during this time.")
            # raise serializers.ValidationError({
            #     "non_field_errors": [f"Room '{room}' is already occupied during this time."]
            # })

        if errors:
            print(f"❌ Conflicts found: {errors}")
            raise serializers.ValidationError({"non_field_errors": errors})


        print("✅ Validation passed — no conflicts found")
        return attrs
