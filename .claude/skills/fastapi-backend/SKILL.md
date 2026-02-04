---
name: fastapi-backend
description: FastAPI best practices — routers, Pydantic v2 models, dependencies, async endpoints, error handling, OpenAPI docs, structure recommendations.
version: 1.0
tags: [fastapi, python, api, backend]
---

# FastAPI Backend Skill

**When to use**:
- Creating API endpoints, routers
- Defining request/response schemas
- Dependencies, middleware, background tasks

**Core Guidelines**:
- FastAPI >= 0.110, Python 3.11+
- Pydantic v2 everywhere
- Async def endpoints
- Folder structure: app/routers/, app/schemas/, app/dependencies/, app/services/
- APIRouter with prefix + tags
- Response models + status codes explicit
- HTTPException for errors
- Dependencies: for auth (but don't implement here), db session etc.
- OpenAPI: summary, description, examples

**Common Patterns**:
- from fastapi import APIRouter, Depends
- router = APIRouter(prefix="/users", tags=["users"])
- class UserCreate(BaseModel): ...
- @router.post("/", response_model=UserOut)

**Anti-patterns**:
- Sync blocking calls in async endpoints
- Missing response_model
- No dependency injection for reusable code

Use this when backend logic write kar rahe ho.