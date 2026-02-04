---
name: database-design
description: PostgreSQL schema design, Prisma schema patterns, relations, migrations, query optimization, indexing best practices.
version: 1.0
tags: [prisma, postgres, database, schema]
---

# Database Design Skill

**When to use**:
- Defining models / schema.prisma
- Relations (1:1, 1:N, N:N)
- Migrations, seed data
- Writing safe/efficient queries

**Core Guidelines**:
- PostgreSQL default
- Prisma ORM for Next.js
- UUIDv7 for IDs (or auto-increment if simple)
- createdAt/updatedAt with @default(now()) @updatedAt
- Relations: @@map, @@unique, @@index
- Enums for roles/status
- Soft deletes: deletedAt DateTime?

**Common Patterns**:
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  role      Role     @default(USER)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

**Anti-patterns**:
- Over-normalization early
- Missing indexes on frequent where/order fields
- Raw SQL when Prisma sufficient

Use when schema change ya query likh rahe ho.