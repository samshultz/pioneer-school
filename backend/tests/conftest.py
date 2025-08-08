import pytest
from rest_framework.test import APIClient
from users.models import Organization


@pytest.fixture
def api_client():
    """Provides DRF APIClient for testing."""
    return APIClient()


@pytest.fixture
def organization(db):
    """Creates a test organization for use in tests."""
    return Organization.objects.create(name="Test School")
