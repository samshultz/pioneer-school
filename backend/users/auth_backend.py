from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import Membership

User = get_user_model()

# class UsernameOrPhoneBackend(ModelBackend):
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         org = kwargs.get("organization")
#         try:
#             user = User.objects.get(
#                 ({"username": username} if username else {"phone": username})
#             )
#         except User.DoesNotExist:
#             return None

#         if org:
#             # ensure user is a member of that organization
#             if not Membership.objects.filter(user=user, organization=org).exists():
#                 return None

#         if user.check_password(password):
#             return user
#         return None


class UsernameOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        org = kwargs.get("organization")

        try:
            if username.isdigit():  # assume digits = phone
                user = User.objects.get(phone=username)
            else:
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        if org:
            if not Membership.objects.filter(user=user, organization=org).exists():
                return None

        if user.check_password(password):
            return user
        return None