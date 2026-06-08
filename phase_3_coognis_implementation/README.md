# PhD Dissertation Appendix Materials: Methodology Phase 3

This folder contains a `Phase 3 – System Implementation and Modular Architecture` materials in a form of **minimum viable reproducible COOGNIS appendix package** intended for dissertation use. Its purpose is not to preserve the full production deployment, but to preserve a **safe, inspectable, and partially runnable prototype** that demonstrates the implemented architecture from Phase 3 without exposing secrets, production delivery infrastructure, or bundled machine-learning artifacts.

The implementation materials included in this phase represent a limited proof-of-feasibility research package intended to support scientific reproducibility of the dissertation while intentionally excluding production-oriented components related to future system development.

The package is deliberately constrained:

- **no real environment variables**
- **no production login flow**
- **no registration flow**
- **no email delivery**
- **no bundled SYNAPSE model artifacts**
- **no production database dump**

The machine-learning artifacts are intentionally excluded because they are reproduced separately in:

- `../phase_2_psychological_profiling`

This appendix package is therefore designed to satisfy two different goals:

1. provide a **runnable mock prototype** of the COOGNIS frontend behavior,
2. provide a **curated backend source snapshot** that documents the implemented Phase 3 architecture.

## Folder Structure

| Path | Role |
|---|---|
| `frontend_prototype/` | Runnable frontend-only prototype using mock services and auto-seeded mock authentication |
| `backend_source/` | Curated backend source snapshot for architectural traceability |
| `docs_reference/` | Supporting evaluation and domain-taxonomy documents referenced by the implementation |

## What Is Included

### 1. Runnable frontend prototype

The frontend prototype is copied from the main COOGNIS frontend and adjusted so that it can be opened **without login or registration**.

Key prototype behaviors:

- mock authentication is enabled
- a mock user session is auto-created on startup
- the application opens directly into the main application area
- no real backend is required for the core demonstration
- chat, user, and admin/expert service responses come from the existing mock-service layer

### 2. Backend source snapshot

The backend source snapshot includes:

- FastAPI application code
- routes
- services
- schemas
- SQLAlchemy models
- Alembic migrations
- backend scripts

This snapshot is included for **code appendix and architectural inspection purposes**.

It is **not guaranteed to run out-of-the-box** because:

- database setup is still required
- SYNAPSE model artifacts are intentionally absent
- mail delivery has been disabled at configuration level
- the production authentication flow is not the focus of this appendix package

### 3. Supporting documentation

Selected documentation files are included because they materially support understanding of the implementation:

- evaluation harness
- benchmark cases
- local LLM runtime notes
- UEX domain taxonomy

## What Is Intentionally Excluded

| Excluded item | Reason |
|---|---|
| Real `.env` files | Security and non-reproducible deployment coupling |
| SMTP credentials / OpenAI keys / production URLs | Security and dissertation appendix minimalism |
| Bundled SYNAPSE `.joblib` artifacts | Reproduced separately in Phase 2 |
| Database dump | Contains operational data and is not necessary for the appendix prototype |
| Backend virtual environments / frontend build artifacts / `node_modules` | Not suitable for archival appendix material |

## Runnable Path

## Frontend Prototype Only

This is the **recommended reproducible path** for the dissertation appendix.

### Requirements

- Node.js `20+`
- npm

The included `.nvmrc` can be used to align the Node version.

### Setup

```bash
cd phase_3_coognis_implementation/frontend_prototype
cp .env.example .env
npm install
npm run dev
```

Then open the local Vite URL, usually:

```text
http://localhost:5173
```

### Prototype Authentication Behavior

The prototype does **not** require:

- login
- registration
- email verification
- two-factor setup

Instead, the frontend auto-seeds a mock authenticated session from environment variables.

By default, the application starts as a mock **user** account and redirects directly into the application.

### Switching Prototype Role

In `frontend_prototype/.env`, you can change:

```env
VITE_PROTOTYPE_ROLE=user
```

Supported values:

- `user`
- `expert`
- `admin`

The route guard will redirect to the corresponding dashboard automatically.

## Optional Backend Reconstruction Path

The backend snapshot is included primarily as **appendix code evidence**, but a partial reconstruction is possible.

### Requirements

- Python `3.12`
- PostgreSQL
- manually supplied Phase 2 SYNAPSE artifacts

### Minimal setup concept

```bash
cd phase_3_coognis_implementation/backend_source
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Important limitation

This backend path will only become meaningfully functional if you also restore the missing profiling model artifacts from Phase 2 into:

```text
backend_source/models/synapse/
```

Those artifacts are **not** included here by design.

### Why the backend is not the primary runnable path

The Phase 3 appendix is meant to be safe and academically reproducible, not to preserve a production environment. For that reason:

- email is forced into non-delivery mode
- no live secrets are used
- no real authentication onboarding is required
- no production ML binaries are embedded

Accordingly, the **frontend prototype** is the main runnable artifact, while the backend snapshot is the main architectural code appendix.

## Files Added for Appendix Reproducibility

### `frontend_prototype/.env.example`

This file is configured for:

- mock auth enabled
- no 2FA requirement
- auto-seeded prototype user
- no real backend dependency

### `backend_source/.env.example`

This file is configured for:

- development-only local values
- `EMAIL_DELIVERY_MODE=log`
- mock/shared-safe runtime defaults
- no live keys

## Implementation Adjustments Made for the Appendix Package

The appendix prototype differs from the full repository in these deliberate ways:

1. **Auto-seeded mock session**
   - the prototype creates a mock authenticated user automatically
   - this removes the need for login and registration pages during demonstration

2. **Root route redirected into application flow**
   - the prototype opens directly into the application area
   - unmatched routes also fall back to the application rather than the login screen

3. **No real secrets**
   - no live `.env` values are copied
   - only safe example environment files are provided

4. **No embedded ML artifacts**
   - the profiling logic remains visible in source
   - the actual Phase 2 artifacts are intentionally omitted

## Recommended Dissertation Use

For the dissertation appendix, this package should be described as:

- a **minimum viable reproducible COOGNIS implementation package**
- containing a **frontend-executable mock prototype**
- plus a **curated backend source snapshot**
- with **machine-learning artifacts separated into Phase 2**

This framing is technically accurate and avoids overclaiming full production reproducibility where production dependencies were intentionally excluded.

## Relationship to the Full Repository

This appendix package was extracted from the full COOGNIS implementation repository and reduced for dissertation-safe archival use.

It preserves:

- implemented architecture
- module structure
- route and service organization
- key frontend interaction patterns
- evaluation support documents

It does not preserve:

- operational deployment state
- production credentials
- bundled model binaries
- real user data
