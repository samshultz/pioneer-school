from core.utils import (
    set_current_organization, 
    get_current_organization
)


class OrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("\n=== [OrganizationMiddleware] Running ===")
        set_current_organization(None)
        request.organization = None

        user = request.user
        print(f"User in middleware: {user} (authenticated={getattr(user, 'is_authenticated', False)})")

        if user and user.is_authenticated:
            from users.models import Membership
            membership = Membership.all_objects.filter(
                user=user, 
                is_active=True
            ).first()
            print(f"First active membership: {membership}")
            if membership:
                org = membership.organization
                print(f"✅ Default org set to {org}")
                set_current_organization(org)
                request.organization = org

        # Allow override via request header
        org_id = request.headers.get("X-Organization-ID")
        print(f"Header X-Organization-ID: {org_id}")
        if org_id and user and user.is_authenticated:
            try:
                from users.models import Organization, Membership
                org = Organization.objects.get(id=org_id)
                if Membership.all_objects.filter(user=user, organization=org).exists():
                    print(f"✅ Overriding org to {org}")
                    set_current_organization(org)
                    request.organization = org
                else:
                    print(f"❌ User is not a member of {org}")
            except Organization.DoesNotExist:
                print(f"❌ Org with id={org_id} does not exist")

        print(f"Final resolved org for request: {get_current_organization()} / {getattr(request, 'organization', None)}")
        print("========================================\n")

        response = self.get_response(request)
        return response
