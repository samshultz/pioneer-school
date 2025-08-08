import pytest
from rest_framework.test import APIClient
from users.models import (
    User, 
    Membership,
    Organization, 
    StudentProfile, 
    TeacherProfile, 
    ParentProfile, 
    PrincipalProfile, 
    AdminProfile
)
from core.utils import (
    set_current_organization, 
    get_current_organization
)

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def organization(db):
    return Organization.objects.create(name="Test School")

@pytest.fixture
def another_organization(db):
    return Organization.objects.create(name="Another School")

@pytest.mark.django_db
def test_registration(api_client, organization):
    response = api_client.post("/api/auth/register/", {
        "email": "student@test.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "1234567890",
        "password": "testpass123",
        "organization": organization.id,
        "role": "STUDENT",  # Must match Membership.RoleChoices.STUDENT
    }, format="json")

    assert response.status_code == 201, response.content
    data = response.json()
    assert "user_id" in data
    assert User.objects.filter(email="student@test.com").exists()
    assert Membership.all_objects.filter(
        user__email="student@test.com", 
        organization=organization
    ).exists()


@pytest.mark.django_db
def test_login_with_email(api_client, organization):
    # create user + membership manually
    user = User.objects.create_user(
        email="teacher@test.com",
        first_name="Jane",
        last_name="Doe",
        password="testpass123",
    )
    Membership.objects.create(user=user, organization=organization, role=Membership.RoleChoices.TEACHER)

    response = api_client.post("/api/auth/login/", {
        "username": "teacher@test.com",  # email login
        "password": "testpass123",
        "organization": organization.id,
    }, format="json")

    assert response.status_code == 200, response.content
    data = response.json()
    assert "access" in data
    assert "refresh" in data


@pytest.mark.django_db
def test_login_with_phone(api_client, organization):
    # create user + membership manually
    user = User.objects.create_user(
        email="parent@test.com",
        first_name="Sam",
        last_name="Smith",
        phone="9876543210",
        password="testpass123",
    )
    Membership.objects.create(user=user, organization=organization, role=Membership.RoleChoices.PARENT)

    response = api_client.post("/api/auth/login/", {
        "username": "9876543210",  # phone login
        "password": "testpass123",
        "organization": organization.id,
    }, format="json")

    assert response.status_code == 200, response.content
    data = response.json()
    assert "access" in data
    assert "refresh" in data


@pytest.mark.django_db
def test_registration_with_username(api_client, organization):
    response = api_client.post("/api/auth/register/", {
        "email": "uniqueuser@test.com",
        "first_name": "Alex",
        "last_name": "Miller",
        "username": "alexm",
        "password": "testpass123",
        "organization": organization.id,
        "role": "TEACHER",
    }, format="json")

    assert response.status_code == 201
    data = response.json()
    assert User.objects.filter(email="uniqueuser@test.com").exists()
    assert Membership.all_objects.filter(user_id=data["user_id"], organization=organization).exists()


@pytest.mark.django_db
def test_registration_fails_without_username_and_phone(api_client, organization):
    response = api_client.post("/api/auth/register/", {
        "email": "fail@test.com",
        "first_name": "No",
        "last_name": "PhoneOrUsername",
        "password": "testpass123",
        "organization": organization.id,
        "role": "STUDENT",
    }, format="json")

    assert response.status_code == 400
    assert "You must provide either a username or a phone number." in str(response.content)


@pytest.mark.django_db
def test_login_with_wrong_password(api_client, organization):
    user = User.objects.create_user(
        email="wrongpass@test.com",
        first_name="Wrong",
        last_name="Pass",
        password="correctpass",
    )

    Membership.all_objects.create(user=user, organization=organization, role=Membership.RoleChoices.STUDENT)

    response = api_client.post("/api/auth/login/", {
        "username": "wrongpass@test.com",
        "password": "incorrectpass",
        "organization": organization.id,
    }, format="json")

    assert response.status_code == 400
    assert "Invalid credentials" in str(response.content)


@pytest.mark.django_db
def test_login_with_nonexistent_user(api_client, organization):
    response = api_client.post("/api/auth/login/", {
        "username": "idontexist@test.com",
        "password": "somepass",
        "organization": organization.id,
    }, format="json")

    assert response.status_code == 400
    assert b"Invalid credentials" in response.content


@pytest.mark.django_db
def test_login_with_wrong_org(api_client, organization, another_organization):
    user = User.objects.create_user(
        email="teacher2@test.com",
        first_name="Jane",
        last_name="WrongOrg",
        password="testpass123",
    )
    # Belongs only to `another_organization`, not the test one
    Membership.objects.create(user=user, organization=another_organization, role=Membership.RoleChoices.TEACHER)

    response = api_client.post("/api/auth/login/", {
        "username": "teacher2@test.com",
        "password": "testpass123",
        "organization": organization.id,  # wrong org
    }, format="json")

    assert response.status_code == 400
    assert b"User not part of this organization" in response.content


@pytest.mark.django_db
def test_login_with_correct_org(api_client, organization):
    user = User.objects.create_user(
        email="insideorg@test.com",
        password="testpass123",
        first_name="Jane",
        last_name="WrongOrg",
    )
    Membership.all_objects.create(user=user, organization=organization, role=Membership.RoleChoices.TEACHER)

    response = api_client.post("/api/auth/login/", {
        "username": "insideorg@test.com",
        "password": "testpass123",
        "organization": organization.id,
    }, format="json")

    assert response.status_code == 200
    assert "access" in response.json()
    assert "refresh" in response.json()


@pytest.mark.django_db
@pytest.mark.parametrize("role,profile_model", [
    ("STUDENT", StudentProfile),
    ("TEACHER", TeacherProfile),
    ("PARENT", ParentProfile),
    ("PRINCIPAL", PrincipalProfile),
    ("ADMIN", AdminProfile),
])
def test_registration_creates_correct_profile(api_client, organization, role, profile_model):
    """Ensure the right profile is created when registering with a specific role."""
    email = f"{role.lower()}@test.com"
    response = api_client.post("/api/auth/register/", {
        "email": email,
        "first_name": "Test",
        "last_name": role.title(),
        "phone": "1234567890",
        "password": "testpass123",
        "organization": organization.id,
        "role": role,
    }, format="json")

    assert response.status_code == 201, response.content
    data = response.json()

    # Check user exists
    user = User.objects.get(id=data["user_id"])
    assert user.email == email

    # Check membership exists
    assert Membership.all_objects.filter(user=user, organization=organization, role=role).exists()

    # Check profile exists
    assert profile_model.objects.filter(membership__user=user, membership__organization=organization).exists()


@pytest.mark.django_db
def test_duplicate_email_registration_fails(api_client, organization):
    """Ensure duplicate email is not allowed."""
    User.objects.create_user(
        email="duplicate@test.com", 
        password="testpass123",
        first_name="Dup",
        last_name="User"
    )

    response = api_client.post("/api/auth/register/", {
        "email": "duplicate@test.com",
        "first_name": "Dup",
        "last_name": "User",
        "phone": "5550001111",
        "password": "testpass123",
        "organization": organization.id,
        "role": "STUDENT",
    }, format="json")

    assert response.status_code == 400
    assert "email" in response.json()


@pytest.mark.django_db
def test_login_with_inactive_membership(api_client, organization):
    user = User.objects.create_user(
        email="inactive@test.com",
        first_name="Inactive",
        last_name="User",
        password="testpass123",
    )
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.RoleChoices.STUDENT,
        is_active=False,  # inactive membership
    )

    response = api_client.post("/api/auth/login/", {
        "username": "inactive@test.com",
        "password": "testpass123",
        "organization": organization.id,
    }, format="json")

    assert response.status_code == 400
    assert b"User not part of this organization" in response.content


@pytest.mark.django_db
def test_studentprofile_isolation_by_org():
    # Create two orgs
    org1 = Organization.objects.create(name="Org One")
    org2 = Organization.objects.create(name="Org Two")

    # Create users + memberships
    user1 = User.objects.create_user(email="s1@test.com", first_name="S1", last_name="User", password="pass123")
    m1 = Membership.objects.create(user=user1, organization=org1, role=Membership.RoleChoices.STUDENT)
    StudentProfile.objects.create(membership=m1, grade="Grade 5")

    user2 = User.objects.create_user(email="s2@test.com", first_name="S2", last_name="User", password="pass123")
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