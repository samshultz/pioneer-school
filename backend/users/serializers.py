from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

from .models import (
    Membership, 
    StudentProfile, 
    TeacherProfile, 
    ParentProfile, 
    PrincipalProfile, 
    AdminProfile,
    Organization
)

User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())
    role = serializers.ChoiceField(choices=Membership.RoleChoices.choices)

    username = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = [
            "id", 
            "email", 
            "first_name", 
            "last_name", 
            "username", 
            "phone", 
            "password", 
            "organization", 
            "role"
        ]
        
    def validate(self, data):
        if not data.get("username") and not data.get("phone"):
            raise serializers.ValidationError("You must provide either a username or a phone number.")
        return data

    def create(self, validated_data):
        password = validated_data.pop("password")
        org = validated_data.pop("organization")
        role = validated_data.pop("role")

        user = User.objects.create_user(
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=password,
            phone=validated_data.get("phone"),
            #username=validated_data.get("username", None),
        )


        # Create membership
        membership = Membership.objects.create(
            user=user, 
            organization=org, 
            role=role
        )

        # Role-based profile
        if role == Membership.RoleChoices.STUDENT:
            StudentProfile.objects.create(membership=membership)
        elif role == Membership.RoleChoices.TEACHER:
            TeacherProfile.objects.create(membership=membership)
        elif role == Membership.RoleChoices.PARENT:
            ParentProfile.objects.create(membership=membership)
        elif role == Membership.RoleChoices.PRINCIPAL:
            PrincipalProfile.objects.create(membership=membership)
        elif role == Membership.RoleChoices.ADMIN:
            AdminProfile.objects.create(membership=membership)

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the default username/email field from SimpleJWT
        if "email" in self.fields:
            self.fields.pop("email")

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        membership = Membership.objects.filter(user=user, is_active=True).first()
        if membership:
            token["organization_id"] = str(membership.organization.id)

        return token
    
    def validate(self, attrs):
        username_or_phone = self.context["request"].data.get("username")  # force read from request
        password = self.context["request"].data.get("password")
        org_id = self.context["request"].data.get("organization")

        if not username_or_phone or not password:
            raise serializers.ValidationError("Both username/phone and password are required")

        try:
            if "@" in username_or_phone:  # treat as email
                user = User.objects.get(email=username_or_phone)
            elif username_or_phone.isdigit():  # treat as phone
                user = User.objects.get(phone=username_or_phone)
            else:
                user = User.objects.get(email=username_or_phone)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        membership = None
        if org_id is not None:
            try:
                org_id = int(org_id)
            except (ValueError, TypeError):
                raise serializers.ValidationError({"organization": "Invalid organization id"})

            memberships = Membership.all_objects.filter(
                user=user, 
                organization_id=org_id,
                is_active=True
            )

            if not memberships.exists():
                raise serializers.ValidationError({"non_field_errors": ["User not part of this organization"]})
            membership = memberships.first()

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")
        
        refresh = self.get_token(user)
        org_id_response = str(membership.organization.id) if membership else refresh.get("organization_id")

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user_id": user.id,
            "email": user.email,
            "phone": user.phone,
            "organization_id": org_id_response,
        }

