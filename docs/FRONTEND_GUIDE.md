# STAIL Realty OS — Frontend Architecture Guide

The frontend application is built as a single-page application (SPA) using React, TypeScript, Vite, Tailwind CSS, and Zustand.

---

## Directory Structure

```
frontend/
├── src/
│   ├── api/             # API client modules (auth, property, crm, agents)
│   ├── components/      # Reusable UI components & layouts
│   ├── pages/           # Route views (Dashboard, Search, Leads, Detail)
│   ├── stores/          # Zustand global state stores (authStore, chatStore)
│   ├── types/           # TypeScript interfaces & types
│   ├── App.tsx          # Main router & routes definition
│   └── main.tsx         # Entrypoint
```

---

## Key Pages & Routes

| Path | View Component | Access Role |
|---|---|---|
| `/login` | `LoginPage` | Public |
| `/register` | `RegisterPage` | Public |
| `/dashboard` | `DashboardPage` | Authenticated |
| `/search` | `SearchPage` (AI Chat) | Authenticated |
| `/properties` | `PropertiesPage` | Public / Authenticated |
| `/history` | `HistoryPage` | Authenticated |
| `/crm/leads` | `CrmLeadsPage` | Broker / Admin |

---

## State Management (Zustand)

### 1. `authStore`
- **State**: `user`, `accessToken`, `isAuthenticated`
- **Actions**: `login(tokens, user)`, `logout()`, `updateUser(user)`

### 2. `chatStore`
- **State**: `messages`, `sessionId`, `isLoading`, `recommendedProperties`
- **Actions**: `sendMessage(text)`, `clearMessages()`, `resumeSession(sessionId)`

---

## Styling Conventions

- **Color Palette**: Dark mode slate primary background (`bg-slate-900`), blue highlight accents (`text-blue-500`).
- **Glassmorphism**: Subtle translucent cards with `backdrop-blur-md bg-slate-800/80 border border-slate-700`.
