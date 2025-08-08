# core/managers.py
from django.db import models
from core.utils import get_current_organization

class OrganizationManager(models.Manager):
    """
    Manager that automatically filters by the current organization
    set in thread-local storage via OrganizationMiddleware.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        org = get_current_organization()
        if org is not None:
            if "organization" in [f.name for f in self.model._meta.fields]:
                return qs.filter(organization=org)
            # If the model has a relation to Membership, filter through it
            if "membership" in [f.name for f in self.model._meta.fields]:
                return qs.filter(membership__organization=org)
            
        return qs
    
    def for_organization(self, organization):
        """
        Explicitly filter by a given organization (ignores thread-local).
        """
        qs = super().get_queryset()
        if "organization" in [f.name for f in self.model._meta.fields]:
            return qs.filter(organization=organization)
        if "membership" in [f.name for f in self.model._meta.fields]:
            return qs.filter(membership__organization=organization)
        return qs
    
