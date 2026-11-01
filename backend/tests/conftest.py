import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.security import create_access_token
from backend.app.db.base import Base
from backend.app.db.models import Organization, OrganizationMember, Repository, User
from backend.app.db.session import get_db
from backend.app.main import app

# In-memory SQLite database for isolated test execution
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session):
    import backend.app.api.v1.routes.pull_requests as pr_route
    import backend.app.api.v1.routes.webhooks as webhooks_route
    
    orig_wh_session = webhooks_route.SessionLocal
    orig_pr_session = pr_route.SessionLocal
    webhooks_route.SessionLocal = TestingSessionLocal
    pr_route.SessionLocal = TestingSessionLocal

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    webhooks_route.SessionLocal = orig_wh_session
    pr_route.SessionLocal = orig_pr_session


@pytest.fixture(scope="function")
def tenant_fixture(db_session: Session):
    """
    Creates two distinct organizations (Tenant A and Tenant B) with their own users,
    memberships, and repositories to rigorously test multi-tenancy isolation.
    """
    # Tenant A
    user_a = User(
        email="alice@tenanta.com",
        username="alice_a",
        full_name="Alice Tenant A",
        is_active=True,
    )
    db_session.add(user_a)
    db_session.flush()

    org_a = Organization(slug="tenant-a-corp", name="Tenant A Corp")
    db_session.add(org_a)
    db_session.flush()

    member_a = OrganizationMember(organization_id=org_a.id, user_id=user_a.id, role="owner")
    db_session.add(member_a)

    repo_a = Repository(
        organization_id=org_a.id,
        github_repo_id=1001,
        full_name="tenant-a/service-alpha",
        default_branch="main",
        clone_url="https://github.com/tenant-a/service-alpha.git",
        is_active=True,
    )
    db_session.add(repo_a)

    # Tenant B
    user_b = User(
        email="bob@tenantb.com",
        username="bob_b",
        full_name="Bob Tenant B",
        is_active=True,
    )
    db_session.add(user_b)
    db_session.flush()

    org_b = Organization(slug="tenant-b-corp", name="Tenant B Corp")
    db_session.add(org_b)
    db_session.flush()

    member_b = OrganizationMember(organization_id=org_b.id, user_id=user_b.id, role="owner")
    db_session.add(member_b)

    repo_b = Repository(
        organization_id=org_b.id,
        github_repo_id=2002,
        full_name="tenant-b/service-beta",
        default_branch="main",
        clone_url="https://github.com/tenant-b/service-beta.git",
        is_active=True,
    )
    db_session.add(repo_b)
    db_session.commit()

    token_a = create_access_token(subject=user_a.id, org_id=org_a.id, username=user_a.username)
    token_b = create_access_token(subject=user_b.id, org_id=org_b.id, username=user_b.username)

    return {
        "user_a": user_a,
        "org_a": org_a,
        "repo_a": repo_a,
        "token_a": token_a,
        "user_b": user_b,
        "org_b": org_b,
        "repo_b": repo_b,
        "token_b": token_b,
    }
