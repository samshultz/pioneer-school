from django.utils.deprecation import MiddlewareMixin
from .models import Membership
    

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = request.user
        if user and user.is_authenticated:
            # if user has multiple memberships, we could allow a header to pick active org
            active_membership = Membership.objects.filter(user=user).first()
            if active_membership:
                request.tenant = active_membership.organization
            else:
                request.tenant = None
        else:
            request.tenant = None
