---
id: 1
title: Fix Status Filter Validation Error
stage: red
date: 2026-02-05
surface: agent
model: claude-sonnet-4-5-20250929
feature: tasks
branch: master
user: Your Name
command: /sp.phr
labels: [bug-fix, validation, api, frontend, backend]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - frontend/lib/api.ts
tests:
 - none
---

## Prompt

--title "Fix-Status-Filter-Validation-Error" --stage "red" --feature "tasks"

## Response snapshot

Fixed a validation error where the frontend was sending a query parameter named 'status' but the backend endpoint expected 'status_filter'. This mismatch caused FastAPI to reject requests with 422 validation errors. Changed the parameter name in the API client to match the backend function parameter.

## Outcome

- ✅ Impact: Resolved 422 validation error occurring on Vercel deployment when accessing tasks page
- 🧪 Tests: none
- 📁 Files: Updated frontend/lib/api.ts line 231 to send 'status_filter' instead of 'status'
- 🔁 Next prompts: none
- 🧠 Reflection: Query parameter names must exactly match FastAPI function parameter names for proper validation

## Evaluation notes (flywheel)

- Failure modes observed: FastAPI validation rejects query parameters with mismatched names, leading to confusing error messages that only appear in production
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add validation in API client to ensure parameter name consistency