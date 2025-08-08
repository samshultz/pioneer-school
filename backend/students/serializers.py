from rest_framework import serializers
from users.models import Membership, StudentProfile


class StudentProfileSerializer(serializers.ModelSerializer):
    membership_id = serializers.PrimaryKeyRelatedField(
        queryset=Membership.objects.all(), source="membership", write_only=True
    )
    student_email = serializers.EmailField(source="membership.user.email", read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "membership_id",
            "student_email",
            "student_name",
            "admission_number",
            "grade",
            "section",
            "parent_contact",
            "date_of_admission",
        ]

    def get_student_name(self, obj):
        return f"{obj.membership.user.first_name} {obj.membership.user.last_name}"

    def validate_membership(self, membership):
        if membership.role != Membership.RoleChoices.STUDENT:
            raise serializers.ValidationError("Membership role must be STUDENT")
        if hasattr(membership, "student_profile"):
            raise serializers.ValidationError("This membership already has a student profile")
        return membership
