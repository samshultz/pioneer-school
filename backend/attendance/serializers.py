from rest_framework import serializers
from .models import (
    AttendanceSession, 
    AttendanceRecord,
    WeeklyAttendanceSummary,
    WeeklyClassAttendanceSummary, 
    TermAttendanceSummary, 
    TermClassAttendanceSummary,
    Holiday
)


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ["id", "date", "description"]
        read_only_fields = ['id']


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.user.get_full_name", 
        read_only=True
    )

    class Meta:
        model = AttendanceRecord
        fields = [
            "id", 
            "student", 
            "student_name", 
            "status", 
            "marked_at", 
            "marked_by"
        ]
        read_only_fields = ["id", "marked_at", "marked_by"]

    def validate(self, attrs):
        request = self.context.get("request")
        session = self.context.get("session")  # we can pass this in from the view if needed
        student = attrs.get("student")

        if not session and "session" in attrs:
            session = attrs["session"]

        if session and student:
            # 1. Ensure student belongs to the same class
            if student.school_class != session.class_ref:
                raise serializers.ValidationError(
                    {"student": "This student does not belong to the class for this session."}
                )

            # 2. Ensure no duplicate attendance for this student in this session
            if AttendanceRecord.objects.filter(
                organization=session.organization, session=session, student=student
            ).exists():
                raise serializers.ValidationError(
                    {"student": "Attendance already marked for this student in this session."}
                )

        return attrs
    
    def create(self, validated_data):
        """Attach organization + user marking the record."""
        request = self.context.get("request")
        if request:
            validated_data["organization"] = request.user.memberships.first().organization
            validated_data["marked_by"] = request.user
        return super().create(validated_data)
    

class AttendanceSessionSerializer(serializers.ModelSerializer):
    class_ref_name = serializers.CharField(source="class_ref.name", read_only=True)
    records = AttendanceRecordSerializer(many=True, read_only=True)

    class Meta:
        model = AttendanceSession
        fields = [
            "id", 
            "class_ref", 
            "class_ref_name", 
            "date", 
            "period",
            "form_teacher", 
            "created_at", 
            "records"
        ]
        read_only_fields = ["id","created_at", "records"]

    def create(self, validated_data):
        request = self.context.get("request")
        records_data = validated_data.pop("records", [])

        if request:
            validated_data["organization"] = request.user.memberships.first().organization

        session = AttendanceSession.objects.create(**validated_data)
        
        for rec in records_data:
            AttendanceRecord.objects.create(
                session=session, 
                organization=session.organization,
                  **rec
            )
        return session

    def update(self, instance, validated_data):
        if instance.is_locked:
            raise serializers.ValidationError(
                "This session is locked and cannot be modified"
            )
        records_data = validated_data.pop("records", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if records_data is not None:
            instance.records.all().delete()
            for rec in records_data:
                AttendanceRecord.objects.create(session=instance, organization=instance.organization, **rec)
        return instance
    
    def validate(self, data):
        """Block sessions on weekends or holidays."""
        class_ref = data.get("class_ref")
        date = data.get("date")
        period = data.get("period")
        form_teacher = data.get("form_teacher")

        organization = (
            self.context["request"].user.memberships.first().organization
            if self.context.get("request") else None
        )

        # Weekend check
        if date.weekday() >= 5:  # 5=Saturday, 6=Sunday
            raise serializers.ValidationError("Cannot create attendance on weekends.")

        # Holiday check
        if organization and Holiday.objects.filter(date=date).exists():
            raise serializers.ValidationError("Cannot create attendance on a holiday.")

        # Duplicate session check
        if organization and AttendanceSession.objects.filter(
            class_ref=class_ref, 
            date=date, 
            period=period
        ).exists():
            raise serializers.ValidationError("Session already exists for this class, date, and period.")
        
        if class_ref and form_teacher and class_ref.form_teacher != form_teacher:
            raise serializers.ValidationError("Form teacher mismatch for this class.")
        
        return data
    

class WeeklyAttendanceSummarySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.user.get_full_name", 
        read_only=True
    )
    class_ref_name = serializers.CharField(
        source="class_ref.name", 
        read_only=True
    )
    class Meta:
        model = WeeklyAttendanceSummary
        fields = [
            "id", 
            "class_ref", 
            "student", 
            "student_name",
            "week_start", 
            "week_end",
            "total_sessions", 
            "attended_sessions", 
            "percentage"
        ]
        read_only_fields = fields

class TermAttendanceSummarySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.user.get_full_name", 
        read_only=True
    )
    class_ref_name = serializers.CharField(
        source="class_ref.name", 
        read_only=True
    )

    class Meta:
        model = TermAttendanceSummary
        fields = [
            "id", 
            "class_ref", 
            "student", 
            "student_name",
            "term", 
            "total_sessions", 
            "attended_sessions", 
            "percentage"
        ]
        read_only_fields = fields

class WeeklyClassAttendanceSummarySerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(
        source="class_ref.name", 
        read_only=True
    )

    class Meta:
        model = WeeklyClassAttendanceSummary
        fields = [
            "id",
            "class_ref",
            "class_name",
            "week_start",
            "week_end",
            "total_sessions",
            "attended_sessions",
            "percentage",
        ]
        read_only_fields = fields


class TermClassAttendanceSummarySerializer(serializers.ModelSerializer):
    class_ref_name = serializers.CharField(
        source="class_ref.name", 
        read_only=True
    )

    class Meta:
        model = TermClassAttendanceSummary
        fields = [
            "id", 
            "organization", 
            "class_ref", 
            "class_ref_name",
            "term",
            "total_sessions", 
            "attended_sessions",
            "male_attendance", 
            "female_attendance",
            "average_percentage"
        ]
        read_only_fields = fields