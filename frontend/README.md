# Offline-First Data Synchronization System (Frontend)

React + Vite + TypeScript + Material UI frontend for the Offline-First Data
Synchronization backend (FastAPI + SQLAlchemy + MySQL + Redis).

The app lets you keep creating, editing, and deleting records while offline.
Changes are queued locally in IndexedDB and synchronized automatically the
moment your connection comes back — with conflict detection and resolution
built in.

---

## Table of contents

- [Tech stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Project setup](#project-setup)
- [Environment variables](#environment-variables)
- [Running the app](#running-the-app)
- [Connecting to the backend](#connecting-to-the-backend)
- [Building for production](#building-for-production)
- [Project structure](#project-structure)
- [How the offline-first flow works](#how-the-offline-first-flow-works)
- [Pages](#pages)
- [Notifications & confirmations](#notifications--confirmations)
- [Testing offline behavior](#testing-offline-behavior)
- [Known assumptions / backend gaps](#known-assumptions--backend-gaps)
- [Troubleshooting](#troubleshooting)

---

## Tech stack

| Layer | Choice |
|---|---|
| Framework | React 18 + Vite 5 |
| Language | TypeScript 5 (strict mode) |
| UI | Material UI v6 — custom dark "SyncGrid" design system (teal / amber / coral / violet status palette, Space Grotesk + Inter + JetBrains Mono) |
| HTTP client | Axios, with a JWT bearer interceptor and auto-redirect to `/login` on 401 |
| Routing | React Router v6, with protected and admin-only route guards |
| Offline storage | IndexedDB via the `idb` wrapper — one store for the record cache, one for the local sync queue |
| Dates | `date-fns` |

---

## Prerequisites

- **Node.js 18 or later** (Node 20 LTS recommended) — check with `node -v`
- **npm 9+** (ships with Node) — check with `npm -v`
- The backend running and reachable (FastAPI + MySQL + Redis). See
  [Connecting to the backend](#connecting-to-the-backend).

You don't need Docker, MySQL, or Redis installed locally to work on the
frontend itself — those are the backend's concern. This project only needs
Node and a reachable API URL.

---

## Project setup

1. **Unzip / clone the project**, then move into it:

   ```bash
   cd frontend
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

   This installs React, MUI, Axios, React Router, `idb`, and the dev
   tooling (TypeScript, Vite, ESLint) listed in `package.json`. No global
   packages are required — everything runs through local `npm` scripts.

3. **Create your local environment file:**

   ```bash
   cp .env.example .env
   ```

   Then open `.env` and point it at your backend (see below).

---

## Environment variables

| Variable | Required | Description | Example |
|---|---|---|---|
| `VITE_API_BASE_URL` | Yes | Base URL of the running FastAPI backend, no trailing slash | `http://localhost:8000` |

`.env.example` ships with a sensible local default:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Notes:

- Vite only exposes env vars prefixed with `VITE_` to client code — this is
  a Vite requirement, not a project choice, so don't rename this variable.
- `.env` is git-ignored. Each environment (local, staging, etc.) should have
  its own `.env` — never commit real values.
- Changing `.env` requires restarting `npm run dev` — Vite reads it once at
  startup.

---

## Running the app

Start the dev server:

```bash
npm run dev
```

This starts Vite on **http://localhost:5173** with hot module reload. Open
that URL in your browser.

Other scripts:

| Command | What it does |
|---|---|
| `npm run dev` | Start the dev server with hot reload |
| `npm run build` | Type-check (`tsc -b`) then produce a production build in `dist/` |
| `npm run preview` | Serve the production build locally, for a final check before deploying |
| `npm run lint` | Run ESLint across the project |

---

## Connecting to the backend

1. Start your backend (FastAPI + MySQL + Redis — via your separate Docker
   Compose setup, or however you normally run it) so it's listening on the
   URL you put in `.env` (e.g. `http://localhost:8000`).
2. Confirm it's reachable: open `http://localhost:8000/health` (or your
   configured URL) in a browser — you should get a JSON `"status": "healthy"`
   response. The frontend polls this exact endpoint to detect connectivity.
3. Confirm CORS is set up on the backend for `http://localhost:5173` and
   `http://127.0.0.1:5173` (it already is, out of the box, in `app/main.py`).
4. Start the frontend with `npm run dev` and open **http://localhost:5173**.
5. Register a new account from the login screen, or log in with an existing
   one seeded on the backend.

If the backend is on a different host/port (a remote server, a different
Docker network, etc.), just update `VITE_API_BASE_URL` in `.env` and restart
`npm run dev`.

---

## Building for production

```bash
npm run build
```

This runs a full TypeScript check and then bundles the app into `dist/` —
a set of static files you can serve from any static host (Nginx, Vercel,
Netlify, an S3 bucket, or the same box as your API behind a reverse proxy).

Before deploying, set `VITE_API_BASE_URL` in your build environment (or a
`.env.production` file) to your real backend URL — Vite bakes it into the
build at build time, not at runtime.

Preview the production build locally before shipping it:

```bash
npm run preview
```

---

## Project structure

```
frontend/
├── index.html                 Vite entry HTML (fonts loaded here)
├── vite.config.ts             Vite config + "@" path alias → src/
├── tsconfig.json              TypeScript config (strict mode)
├── .env.example                Sample environment file
├── package.json
└── src/
    ├── main.tsx                React root, MUI ThemeProvider + CssBaseline
    ├── App.tsx                 Routes, guards, context providers
    ├── vite-env.d.ts           Vite/env typing
    │
    ├── api/                    One file per backend resource (thin Axios wrappers)
    │   ├── client.ts           Axios instance, JWT interceptor, error helper
    │   ├── auth.ts             Login / register / me / profile / password
    │   ├── users.ts            Admin user management
    │   ├── records.ts          Record CRUD (direct/online calls)
    │   ├── sync.ts             Sync operation create/process
    │   ├── conflicts.ts        Conflict list/resolve
    │   ├── dashboard.ts        Stats + sync-operations search
    │   ├── syncHistory.ts      Sync history list
    │   └── auditLogs.ts        Audit log (own + admin "all")
    │
    ├── context/
    │   ├── AuthContext.tsx     Current user, login/register/logout
    │   ├── SyncContext.tsx     Online status, local queue, auto-sync loop
    │   └── NotificationContext.tsx  Global toast (Snackbar) notifications
    │
    ├── db/
    │   ├── indexedDb.ts        IndexedDB schema + CRUD helpers (records, queue, meta)
    │   └── syncEngine.ts       Walks the local queue, talks to the backend, reconciles
    │
    ├── hooks/
    │   ├── useNetworkStatus.ts Real connectivity check (backend ping, not just navigator.onLine)
    │   └── useRecords.ts       Offline-first record CRUD (optimistic cache + queue)
    │
    ├── routes/
    │   └── guards.tsx          ProtectedRoute / AdminRoute / GuestRoute
    │
    ├── theme/
    │   └── theme.ts            "SyncGrid" MUI theme + status color helper
    │
    ├── types/
    │   └── index.ts            Shared TypeScript types, mirroring backend schemas
    │
    ├── components/
    │   ├── layout/             Sidebar, Topbar, AppLayout, NetworkIndicator
    │   ├── common/              StatCard, StatusChip, EmptyState, ConfirmDialog
    │   ├── records/             RecordFormDialog
    │   └── conflicts/           ConflictResolutionDialog
    │
    └── pages/
        ├── LoginPage.tsx / RegisterPage.tsx
        ├── DashboardPage.tsx
        ├── RecordsPage.tsx
        ├── SyncQueuePage.tsx
        ├── ConflictsPage.tsx
        ├── SyncHistoryPage.tsx
        ├── AuditLogPage.tsx
        ├── UsersPage.tsx        (admin only)
        └── ProfilePage.tsx
```

---

## How the offline-first flow works

1. Every record mutation (create/update/delete) writes optimistically to an
   IndexedDB `records` store **and** appends an entry to an IndexedDB
   `queue` store — regardless of whether you're online. This is what makes
   the UI behave identically offline and online.
2. `useNetworkStatus` pings `GET /health` every 15s (plus browser
   online/offline events) to determine real connectivity —
   `navigator.onLine` alone is unreliable, since it only reflects the
   network interface, not whether the API is actually reachable.
3. `SyncContext` runs the sync engine automatically: immediately when
   connectivity is restored, and again on a 20-second interval while
   online.
4. The sync engine (`src/db/syncEngine.ts`) walks the queue in FIFO order,
   registers each operation with `POST /sync/operations` (a 409 there means
   it was already registered — treated as success, which is what makes
   retries safe), then calls `POST /sync/operations/{id}/process`. A
   `CONFLICT` response leaves the queue entry in `CONFLICT` state and does
   **not** drop it — it's picked up by the Conflicts page instead of
   silently failing.
5. Resolving a conflict (Conflicts page) calls
   `POST /conflicts/{id}/resolve` with your chosen strategy (server-wins /
   client-wins / last-write-wins / manual), then reconciles the local
   cache and clears the stuck queue entry.

---

## Pages

- **Dashboard** — live stats from `/dashboard/sync-statistics` plus local
  queue counts (works offline with cached numbers where relevant).
- **Records** — offline-capable CRUD. Rows show a "Queued" vs "Synced" chip.
  Delete requires a confirmation dialog (two-step — no accidental one-click
  deletes).
- **Sync Queue** — every local operation and its current state/attempt
  count.
- **Conflicts** — pending/all conflicts with a side-by-side client-vs-server
  diff, a resolution dialog, a Notes column showing `resolution_notes`, and
  toast confirmation on resolve (success, or the real backend error
  message on failure).
- **Sync History** — full search (operation ID), status/type/date filters,
  sortable columns, and pagination, backed by `/dashboard/sync-operations`.
- **Audit Log** — every action tied to your account (`GET /audit-logs`),
  with action/entity/date filters and pagination. Admins get a "My
  activity / All activity" toggle to also see everyone's log
  (`GET /audit-logs/all`).
- **Users** *(Admin only)* — search, pagination, role change,
  activate/deactivate, edit name & email (`PUT /users/{id}` — password is
  never editable here), and delete (behind a confirmation dialog).
- **Profile** — self-service editing. Update your own name/email
  (`PUT /auth/me`) and change your own password with current-password
  verification (`PUT /auth/me/password`) — no OTP step, matching the
  backend's simple flow.

---

## Notifications & confirmations

- `src/context/NotificationContext.tsx` provides a global `useNotify()`
  hook (a bottom-right Snackbar) used across Profile, Users, Records, and
  Conflicts for success/error feedback — nothing fails silently.
- `src/components/common/ConfirmDialog.tsx` is the shared two-step delete
  confirmation used by both Records and Users — the only two delete
  actions in the app. Nothing deletes on a single click.

---

## Testing offline behavior

Since the frontend and backend usually both run on `localhost` during
development, turning off Wi-Fi does **nothing** — that traffic never leaves
your machine. To actually simulate offline:

1. Open Chrome/Edge DevTools → **Network** tab → set the throttling
   dropdown to **Offline**. This is the most reliable method.
2. Alternatively: DevTools → **Application** tab → **Service Workers** →
   check **Offline**.
3. Or just stop the backend process — the health check will fail and the
   app will flip to "Offline" within ~15 seconds.

With DevTools set to Offline, try creating/editing/deleting a record — it
should still work instantly, show a "Queued" chip, and appear in the Sync
Queue page. Switch back to "No throttling" (or "Online") and watch it sync
automatically within a few seconds.

---

## Known assumptions / backend gaps

1. **`role_id` → role name is inferred, not returned.** `UserResponse` only
   includes `role_id`, not the role's name, so the frontend assumes `1 =
   Admin`, `2 = User` (matching the backend's seed order). If your roles
   table ever gets reseeded in a different order, update `ADMIN_ROLE_ID`
   in `src/context/AuthContext.tsx` and `ROLE_OPTIONS` in
   `src/pages/UsersPage.tsx`.
2. **Redis isn't wired into the sync endpoints themselves**, so
   server-side dedup beyond the `operation_id` unique constraint is
   limited. The frontend's own idempotency (treating a 409 on operation
   creation as "already registered, keep going") is what makes safe
   retries possible today.
3. IndexedDB storage in this app is **not namespaced per user** — it
   assumes one active account per browser profile. Logging in as a
   different user in the same browser will show the previous user's
   offline queue until it's synced or cleared.

---

## Troubleshooting

**Blank page / "Cannot find module '@/...'" errors in the console**
Restart the dev server after any change to `vite.config.ts` or
`tsconfig.json` — path aliases are resolved at startup.

**"Network Error" on every request**
Check `VITE_API_BASE_URL` in `.env`, confirm the backend is running, and
confirm you can hit `<that URL>/health` directly in a browser.

**Login works but every other request 401s immediately**
Your JWT may already be expired (`jwt_access_token_expire_minutes` on the
backend). Log out and back in. This also happens if you switch between
Admin and a regular User account on the same browser while an old token is
cached — see the "not namespaced per user" note above.

**Stuck records showing "Queued" forever**
Check the Sync Queue page — the row's error message will say why (commonly
a 401 from an expired token, or a 404 because the record belongs to a
different account on a shared browser profile). Fix the underlying cause,
then click "Sync now" on any page's top bar.

**A conflict I resolved is still showing as pending**
Make sure you're online — conflict resolution is a server-side call
(`POST /conflicts/{id}/resolve`) and doesn't queue for later.

**TypeScript build fails after pulling changes**
Run `npm install` again — a dependency may have changed — then
`npm run build`.
