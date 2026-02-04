---
name: betterauth-jwt
description: Better Auth library setup + JWT token patterns for Next.js + FastAPI. Session handling, protected routes, OAuth flows, refresh tokens, RBAC basics.
version: 1.0
tags: [auth, better-auth, jwt, nextjs-auth]
---

# Better Auth + JWT Skill

**When to use**:
- Auth config in Next.js
- Login/signup flows
- Session checks, protected pages/APIs
- JWT creation/verification

**Core Guidelines**:
- Better Auth latest for Next.js (auth.ts file)
- JWT access + refresh tokens
- httpOnly, secure cookies
- Backend: PyJWT or fastapi-jwt-auth for verification
- Flows: credentials, OAuth (Google etc.), email verification
- RBAC: roles in session/user object

**Common Patterns**:
- Next.js: import { auth } from "@/auth"; const session = await auth();
- Middleware: export { auth as middleware }
- Backend dependency: async def get_current_user(token: str = Depends(oauth2_scheme))

**Anti-patterns**:
- Storing access tokens in localStorage
- No refresh token rotation
- Weak secret / no expiration

Delegate UI to frontend skill, schema to database skill.