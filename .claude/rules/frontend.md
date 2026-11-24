---
paths:
  - "frontend/**/*.{ts,tsx}"
---

# Frontend rules

- Server components by default. Add `'use client'` only when the component needs state, effects or browser APIs.
- No `any`. Type API responses once in the typed client, do not re-declare them per component.
- All network calls go through the API client module. No raw `fetch` scattered in components.
- Only non-secret values may use the `NEXT_PUBLIC_` prefix.
- Mobile first. Anything you touch must work at 375px width.
- Animations (Framer Motion) respect `prefers-reduced-motion`.
- Interactive elements that e2e tests need get a stable `data-testid`. Prefer accessible roles and names first.
- Handle loading, empty and error states for every data-driven view.
