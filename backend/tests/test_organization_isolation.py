import pytest
from django.test import RequestFactory
from users.models import User, Organization, Membership, StudentProfile
from core.utils import set_current_organization, get_current_organization
from core.middleware import OrganizationMiddleware


@pytest.mark.django_db
def test_studentprofile_isolation_by_org():
    org1 = Organization.objects.create(name="Org One")
    org2 = Organization.objects.create(name="Org Two")

    user1 = User.objects.create_user(
        email="s1@test.com", first_name="S1", last_name="User", password="pass123"
    )
    m1 = Membership.objects.create(user=user1, organization=org1, role=Membership.RoleChoices.STUDENT)
    StudentProfile.objects.create(membership=m1, grade="Grade 5")

    user2 = User.objects.create_user(
        email="s2@test.com", first_name="S2", last_name="User", password="pass123"
    )
    m2 = Membership.objects.create(user=user2, organization=org2, role=Membership.RoleChoices.STUDENT)
    StudentProfile.objects.create(membership=m2, grade="Grade 6")

    # Switch to org1 context
    set_current_organization(org1)
    org1_students = StudentProfile.objects.all()
    assert org1_students.count() == 1
    assert org1_students.first().membership.organization == org1

    # Switch to org2 context
    set_current_organization(org2)
    org2_students = StudentProfile.objects.all()
    assert org2_students.count() == 1
    assert org2_students.first().membership.organization == org2


@pytest.mark.django_db
def test_membership_isolation_by_org():
    org1 = Organization.objects.create(name="School A")
    org2 = Organization.objects.create(name="School B")

    user1 = User.objects.create_user(email="a@test.com", first_name="A", last_name="User", password="pass123")
    Membership.objects.create(user=user1, organization=org1, role=Membership.RoleChoices.TEACHER)

    user2 = User.objects.create_user(email="b@test.com", first_name="B", last_name="User", password="pass123")
    Membership.objects.create(user=user2, organization=org2, role=Membership.RoleChoices.TEACHER)

    # Org1 context
    set_current_organization(org1)
    assert Membership.objects.count() == 1
    assert Membership.objects.first().organization == org1

    # Org2 context
    set_current_organization(org2)
    assert Membership.objects.count() == 1
    assert Membership.objects.first().organization == org2


@pytest.mark.django_db
def test_organization_middleware_sets_current_org():
    """
    Ensure OrganizationMiddleware sets the current organization
    based on the first membership of the logged-in user.
    """
    org = Organization.objects.create(name="Mediators School")
    user = User.objects.create_user(
        email="teacher@test.com", first_name="Jane", last_name="Doe", password="pass123"
    )
    Membership.objects.create(user=user, organization=org, role=Membership.RoleChoices.TEACHER)

    rf = RequestFactory()
    request = rf.get("/")  # simulate request
    request.user = user

    middleware = OrganizationMiddleware(lambda r: r)
    middleware(request)

    # Current org should now be set
    current_org = get_current_organization()
    assert current_org == org


# -------------------------------
# 🔹 Edge Case Tests
# -------------------------------

@pytest.mark.django_db
def test_middleware_no_membership_sets_none():
    """
    If user has no memberships, current org should remain None.
    """
    user = User.objects.create_user(
        email="nomember@test.com", first_name="No", last_name="Member", password="pass123"
    )

    rf = RequestFactory()
    request = rf.get("/")
    request.user = user

    middleware = OrganizationMiddleware(lambda r: r)
    middleware(request)

    assert get_current_organization() is None


@pytest.mark.django_db
def test_middleware_multiple_memberships_picks_first():
    """
    If user has multiple memberships, middleware picks the first one.
    """
    org1 = Organization.objects.create(name="Alpha School")
    org2 = Organization.objects.create(name="Beta School")

    user = User.objects.create_user(
        email="multi@test.com", first_name="Multi", last_name="User", password="pass123"
    )
    m1 = Membership.objects.create(user=user, organization=org1, role=Membership.RoleChoices.TEACHER)
    m2 = Membership.objects.create(user=user, organization=org2, role=Membership.RoleChoices.TEACHER)

    rf = RequestFactory()
    request = rf.get("/")
    request.user = user

    middleware = OrganizationMiddleware(lambda r: r)
    middleware(request)

    current_org = get_current_organization()
    # It should default to the *first* membership
    assert current_org in [org1, org2]  # sanity check
    assert current_org == m1.organization  # Django's .first() should return org1


@pytest.mark.django_db
def test_anonymous_user_sets_none():
    """
    If request.user is anonymous, middleware should leave org as None.
    """
    rf = RequestFactory()
    request = rf.get("/")
    request.user = type("Anonymous", (), {"is_authenticated": False})()  # fake anon user

    middleware = OrganizationMiddleware(lambda r: r)
    middleware(request)

    assert get_current_organization() is None

@pytest.mark.django_db
def test_middleware_inactive_membership_sets_none():
    """
    If user only has inactive memberships, middleware should not set any organization.
    """
    org = Organization.objects.create(name="Dormant School")
    user = User.objects.create_user(
        email="inactiveonly@test.com", first_name="Inactive", last_name="Only", password="pass123"
    )
    Membership.objects.create(
        user=user, organization=org, role=Membership.RoleChoices.STUDENT, is_active=False
    )

    rf = RequestFactory()
    request = rf.get("/")
    request.user = user

    middleware = OrganizationMiddleware(lambda r: r)
    middleware(request)

    assert get_current_organization() is None