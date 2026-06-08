from fastapi import APIRouter

from app.api.routes import admin, auth, expert, feedback, health, mind, page, privacy, synapse, uex, ulm, user

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(expert.router, prefix="/expert", tags=["expert"])
api_router.include_router(mind.router, prefix="/mind", tags=["mind"])
api_router.include_router(synapse.router, prefix="/synapse", tags=["synapse"])
api_router.include_router(uex.router, prefix="/uex", tags=["uex"])
api_router.include_router(ulm.router, prefix="/ulm", tags=["ulm"])
api_router.include_router(page.router, prefix="/page", tags=["page"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(privacy.router, tags=["privacy"])
