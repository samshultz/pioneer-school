# core/utils.py
from threading import local

_user_context = local()

def set_current_organization(org):
    _user_context.organization = org

def get_current_organization():
    return getattr(_user_context, "organization", None)
