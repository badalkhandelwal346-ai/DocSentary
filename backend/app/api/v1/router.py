from fastapi import APIRouter

from backend.app.api.v1.routes import (
    analyses,
    auth,
    evaluations,
    findings,
    github,
    health,
    organizations,
    pull_requests,
    repositories,
    users,
    webhooks,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(github.router)
api_router.include_router(organizations.router)
api_router.include_router(repositories.router)
api_router.include_router(pull_requests.router)
api_router.include_router(analyses.router)
api_router.include_router(findings.router)
api_router.include_router(evaluations.router)
api_router.include_router(webhooks.router)
