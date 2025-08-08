from rest_framework_simplejwt.authentication import JWTAuthentication
from users.models import Membership, Organization
from core.utils import set_current_organization

# class OrganizationJWTAuthentication(JWTAuthentication):
#     """
#     Extends JWTAuthentication to also resolve the active organization
#     for the authenticated user (from JWT or headers).
#     """

#     def authenticate(self, request):
#         # First authenticate user via JWT
#         result = super().authenticate(request)
#         if result is None:
#             return None

#         user, token = result

#         # Default: clear organization
#         request.organization = None
#         set_current_organization(None)

#         # Step 1: Look for org in header
#         org_id = request.headers.get("X-Organization-ID")

#         if org_id:
#             try:
#                 org = Organization.objects.get(id=org_id)
#                 if Membership.all_objects.filter(
#                     user=user, 
#                     organization=org, 
#                     is_active=True
#                 ).exists():
#                     request.organization = org
#                     set_current_organization(org)
#             except Organization.DoesNotExist:
#                 pass

#         # Step 2: If no header org, pick first active membership
#         if not request.organization:
#             membership = Membership.all_objects.filter(
#                 user=user, 
#                 is_active=True
#             ).first()
#             if membership:
#                 org = membership.organization
#                 request.organization = org
#                 set_current_organization(org)

#         return user, token

from rest_framework_simplejwt.authentication import JWTAuthentication
from users.models import Membership, Organization
from core.utils import set_current_organization

class OrganizationJWTAuthentication(JWTAuthentication):
    """
    Extends JWTAuthentication to also resolve the active organization
    from the JWT payload.
    """

    def authenticate(self, request):
        # Authenticate user via base JWTAuthentication
        result = super().authenticate(request)
        if result is None:
            return None

        user, token = result

        # Clear first
        request.organization = None
        set_current_organization(None)

        org_id = token.get("organization_id")

        if org_id:
            try:
                org = Organization.objects.get(id=org_id)
                if Membership.objects.filter(user=user, organization=org, is_active=True).exists():
                    request.organization = org
                    set_current_organization(org)
            except Organization.DoesNotExist:
                pass

        return user, token

