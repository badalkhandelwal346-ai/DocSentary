from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class GitHubAuthRequest(BaseModel):
    code: str
    redirect_uri: Optional[str] = None


class GitHubTokenConnectRequest(BaseModel):
    token: str


class DirectAuthRequest(BaseModel):
    username: str
    password: Optional[str] = "devpassword"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class OrganizationSummary(BaseModel):
    id: str
    slug: str
    name: str
    role: str = "member"

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    onboarding_completed: bool = False
    onboarding_step: int = 1
    has_github_connected: bool = False
    created_at: datetime
    organization: Optional[OrganizationSummary] = None

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class OnboardingStatus(BaseModel):
    onboarding_step: int
    onboarding_completed: bool
    has_github_connected: bool
    connected_repos_count: int


class OnboardingUpdateRequest(BaseModel):
    onboarding_step: Optional[int] = None
    onboarding_completed: Optional[bool] = None
