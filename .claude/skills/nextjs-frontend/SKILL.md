---
name: nextjs-frontend
description: Latest Next.js App Router (v15+) frontend best practices, patterns, component structure, Tailwind + shadcn/ui usage, Server Components priority, performance optimizations, accessibility rules.
version: 1.0
tags: [nextjs, frontend, react, tailwind, ui]
---

# Next.js Frontend Skill

**When Claude should use this skill**:
- Building or editing UI components, pages, layouts
- Styling, responsiveness, forms, loading/error states
- Data fetching in Server Components
- Accessibility or SEO metadata

**Core Guidelines to Follow**:
- App Router only (`app/` dir)
- Server Components default — 'use client' sirf interactivity ke liye
- Tailwind CSS + shadcn/ui / Radix UI prefer
- TypeScript strict mode
- Atomic design / folder-per-component if large
- Forms: React Hook Form + Zod
- Data: fetch() with revalidate / cache options, Suspense boundaries
- Performance: minimal client JS, partial prerendering, streaming
- Accessibility: semantic HTML, ARIA, focus management, contrast
- Dark mode: class strategy ya next-themes

**Common Patterns**:
- Layouts: root layout + nested layouts
- Pages: async function Page() { ... }
- Components: export function MyComponent() { ... }
- Metadata: generateMetadata async

**Anti-patterns to avoid**:
- Overusing 'use client'
- Client-side data fetching when Server Component possible
- Inline styles instead of Tailwind

Reference this skill when writing frontend code.