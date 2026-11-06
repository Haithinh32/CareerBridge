from api import (
    admin,
    analytics,
    applications,
    auth,
    candidate,
    jobs,
    organizations,
    privacy,
    recommendations,
    skills,
)

ROUTERS = [
    auth.router,
    candidate.router,
    jobs.router,
    applications.router,
    applications.profile_router,
    recommendations.router,
    privacy.router,
    organizations.company_router,
    organizations.school_router,
    skills.router,
    analytics.router,
    admin.router,
]
