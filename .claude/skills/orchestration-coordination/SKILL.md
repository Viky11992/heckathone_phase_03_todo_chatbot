---
name: orchestration-coordination
description: Multi-agent task decomposition, delegation patterns, dependency management, progress tracking, synthesis best practices for Claude Code teams. Use when planning or coordinating between Frontend, Backend, Auth, Database agents.
version: 1.0
tags: [orchestrator, coordination, multi-agent, delegation]
---

# Orchestration & Coordination Skill

**When to use this skill**:
- Breaking down user feature requests
- Deciding task order & parallelism
- Writing clear delegation instructions
- Managing dependencies & blocking tasks
- Synthesizing agent outputs

**Core Patterns to Follow**:

1. Task Decomposition
   - Split into atomic steps (schema → API → auth → UI)
   - Identify parallelizable parts (e.g., frontend layout while backend builds API)

2. Dependency Graph (simple text version)
   - Database → Backend + Auth
   - Backend + Auth → Frontend
   - Use phrases: "blocked by", "after", "in parallel with"

3. Delegation Best Practices
   - Give context: "Using the User model from Database Agent..."
   - Be specific: endpoint path, response shape, component name
   - Set output expectation: "Return file paths changed + code diffs"

4. Progress Tracking
   - Maintain mental list: pending / in-progress / completed
   - Ask agents for status if stuck

5. Synthesis Rules
   - Check consistency (naming, types, auth checks)
   - Resolve conflicts (ask agents to align)
   - Produce final integration steps

**Anti-patterns to avoid**:
- Micromanaging agents (give clear objective, not line-by-line)
- Forgetting dependencies → leads to broken code
- Writing code in orchestrator — stay in planning/coordination role

Reference agents:
- @Frontend Agent
- @Backend Agent
- @Auth Agent
- @Database Agent

Use this skill automatically when task involves >1 domain.