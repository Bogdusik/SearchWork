---
paths:
  - "frontend/**"
---

# UI Conventions

Dark aesthetic — do not introduce light backgrounds or white cards.

- **Background:** `#030303` with Spline 3D robot fixed full-screen (`robot-background.tsx`)
- **Cards:** frosted glass — `backdrop-blur`, `bg-white/[0.04]`, `border border-white/[0.08]`
- **Accents:** indigo / rose / violet gradients
- **Mouse effect:** Spotlight component follows cursor (in layout)

When adding new UI components, match the existing frosted glass style. Do not use solid white/light backgrounds.
