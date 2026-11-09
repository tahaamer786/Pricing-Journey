from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from routers import auth_router, plans_router, onboarding_router, persona_router
from config import get_settings

settings = get_settings()

app = FastAPI(
    title="Jubala Onboarding & Pricing API",
    description="""
## Jubala.ai Pricing & Onboarding Journey API

### Flow
1. `GET /api/v1/auth/google/login` — start Google login
2. `GET /api/v1/plans` — show pricing plans
3. `POST /api/v1/users/select-plan` — user picks a plan
4. `POST /api/v1/onboarding/business-info` — submit URL or get questions
5. `POST /api/v1/onboarding/submit-answers` — (if no URL) submit answers
6. `POST /api/v1/persona/generate` — LLM generates the persona report
    """,
    version="1.0.0",
)

# Required for Authlib's OAuth state handling
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(plans_router.router)
app.include_router(onboarding_router.router)
app.include_router(persona_router.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "jubala-onboarding-api"}
