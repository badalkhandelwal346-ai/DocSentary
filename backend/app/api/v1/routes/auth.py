import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.dependencies import get_current_user
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.db.models.organization import Organization
from backend.app.db.models.organization_member import OrganizationMember
from backend.app.db.models.user import User
from backend.app.db.session import get_db
from backend.app.schemas.auth import (
    AuthResponse,
    DirectAuthRequest,
    GitHubAuthRequest,
    LoginRequest,
    OrganizationSummary,
    SignupRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


def _get_or_create_default_org(db: Session, user: User) -> Organization:
    membership = db.scalar(
        select(OrganizationMember).where(OrganizationMember.user_id == user.id)
    )
    if membership:
        org = db.scalar(select(Organization).where(Organization.id == membership.organization_id))
        if org:
            return org

    org_slug = f"{user.username}-workspace"
    org = db.scalar(select(Organization).where(Organization.slug == org_slug))
    if not org:
        org = Organization(
            slug=org_slug,
            name=f"{user.full_name or user.username}'s Team",
        )
        db.add(org)
        db.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role="owner",
    )
    db.add(member)
    db.commit()
    db.refresh(org)
    return org


def _user_to_response(db: Session, user: User) -> UserResponse:
    org = _get_or_create_default_org(db, user)
    membership = db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.user_id == user.id,
            OrganizationMember.organization_id == org.id,
        )
    )
    role = membership.role if membership else "member"

    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        onboarding_completed=user.onboarding_completed,
        onboarding_step=user.onboarding_step,
        has_github_connected=bool(user.github_access_token or user.github_user_id),
        created_at=user.created_at,
        organization=OrganizationSummary(
            id=org.id,
            slug=org.slug,
            name=org.name,
            role=role,
        ),
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Register a new user account with email and password.
    """
    # Check existing email
    existing_email = db.scalar(select(User).where(User.email == payload.email))
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    # Check existing username
    existing_user = db.scalar(select(User).where(User.username == payload.username))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken. Please choose another.",
        )

    hashed = hash_password(payload.password)
    new_user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name or payload.username,
        hashed_password=hashed,
        is_active=True,
        onboarding_completed=False,
        onboarding_step=1,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    org = _get_or_create_default_org(db, new_user)
    token = create_access_token(subject=new_user.id, org_id=org.id, username=new_user.username)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_user_to_response(db, new_user),
    )


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Authenticate with username/email and password.
    """
    user = db.scalar(
        select(User).where(
            or_(
                User.username == payload.username_or_email,
                User.email == payload.username_or_email,
            ),
            User.is_active == True,
        )
    )
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
        )

    org = _get_or_create_default_org(db, user)
    token = create_access_token(subject=user.id, org_id=org.id, username=user.username)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_user_to_response(db, user),
    )


@router.post("/direct", response_model=AuthResponse)
def direct_login(
    payload: DirectAuthRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Direct developer login for local development and test automation.
    """
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user:
        user = User(
            email=f"{payload.username}@example.com",
            username=payload.username,
            full_name=payload.username.capitalize(),
            is_active=True,
            onboarding_completed=False,
            onboarding_step=1,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    org = _get_or_create_default_org(db, user)
    token = create_access_token(subject=user.id, org_id=org.id, username=user.username)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_user_to_response(db, user),
    )


@router.post("/github", response_model=AuthResponse)
def github_auth(
    payload: GitHubAuthRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Exchanges GitHub OAuth temporary code for user session and stores GitHub access token.
    """
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "GitHub OAuth is not configured on this server. "
                "Please configure DOCSENTRY_GITHUB_CLIENT_ID and DOCSENTRY_GITHUB_CLIENT_SECRET in .env, "
                "or use direct developer authentication for local development."
            ),
        )

    try:
        token_resp = httpx.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": payload.code,
                "redirect_uri": payload.redirect_uri,
            },
            timeout=10.0,
        )
        token_data = token_resp.json()
        gh_token = token_data.get("access_token")
        if not gh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitHub token exchange failed: {token_data.get('error_description', 'Invalid code')}",
            )

        # Fetch GitHub User profile
        user_resp = httpx.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {gh_token}", "Accept": "application/json"},
            timeout=10.0,
        )
        gh_user = user_resp.json()
        gh_id = str(gh_user.get("id"))
        username = gh_user.get("login")
        email = gh_user.get("email") or f"{username}@users.noreply.github.com"
        avatar_url = gh_user.get("avatar_url")
        full_name = gh_user.get("name") or username

        # Upsert user
        user = db.scalar(select(User).where(User.github_user_id == gh_id))
        if not user:
            user = db.scalar(select(User).where(User.username == username))

        if user:
            user.github_user_id = gh_id
            user.avatar_url = avatar_url
            user.full_name = full_name
            user.github_access_token = gh_token
        else:
            user = User(
                email=email,
                username=username,
                full_name=full_name,
                avatar_url=avatar_url,
                github_user_id=gh_id,
                github_access_token=gh_token,
                is_active=True,
                onboarding_completed=False,
                onboarding_step=2,
            )
            db.add(user)

        db.commit()
        db.refresh(user)

        org = _get_or_create_default_org(db, user)
        token = create_access_token(subject=user.id, org_id=org.id, username=user.username)

        return AuthResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=_user_to_response(db, user),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("GitHub OAuth exchange exception: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitHub OAuth error: {str(exc)}",
        ) from exc


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    return _user_to_response(db, current_user)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)) -> dict:
    return {"status": "logged_out", "username": current_user.username}
