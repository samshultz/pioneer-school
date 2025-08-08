from rest_framework import serializers
from users.models import TeacherProfile, Membership


class TeacherProfileSerializer(serializers.ModelSerializer):
    # Show teacher’s name and email from Membership → User
    email = serializers.EmailField(source="membership.user.email", read_only=True)
    first_name = serializers.CharField(source="membership.user.first_name", read_only=True)
    last_name = serializers.CharField(source="membership.user.last_name", read_only=True)


    membership_id = serializers.PrimaryKeyRelatedField(
        source="membership",
        queryset=Membership.objects.filter(role=Membership.RoleChoices.TEACHER),
        write_only=True
    )

    class Meta:
        model = TeacherProfile
        fields = [
            "id",
            "membership_id",
            "email",
            "first_name",
            "last_name",
            "employee_id",
            "specialization",
            "hire_date",
            "qualifications",
        ]


class TeacherProfileCreateSerializer(serializers.ModelSerializer):
    """
    Used for creation – requires membership_id since it links TeacherProfile <-> Membership
    """
    membership_id = serializers.PrimaryKeyRelatedField(
        queryset=Membership.objects.filter(role=Membership.RoleChoices.TEACHER),
        source="membership",
        write_only=True
    )

    class Meta:
        model = TeacherProfile
        fields = [
            "id",
            "membership_id",
            "employee_id",
            "specialization",
            "hire_date",
            "qualifications",
        ]
