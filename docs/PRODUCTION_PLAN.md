# Production plan: accounts, hosting, phones, camera

How to turn the local prototype into a real website and phone app: people sign in with their
email, their library follows them between phone and computer, and they can photograph pages
with the camera.

Status: **proposal** · 2026-11-04. Each phase ends in a working, deployable state.
Decisions still open are listed at the end; the plan states a recommended default for each.

---

## 1. Where we are and where we're going

| Concern | Prototype (today) | Target |
|---|---|---|
| Users | none; one library for whoever opens the page | email accounts (magic link), every row belongs to a user |
| Data | SQLite file `backend/data/library.sqlite` | Postgres |
| Pictures | `data:` URIs inside each document's HTML | files in object storage, documents reference them by id |
| OCR | synchronous request, models in the API process, `gpu_lock` | job queue + separate worker process |
| Hosting | `uvicorn` on a Mac, `localhost:8000` | Docker on a server, HTTPS, CI/CD, backups, monitoring |
| Clients | desktop browser, mouse-driven | responsive website → installable PWA → optional iOS/Android apps |
| Camera | file picker only | phone camera capture, later an in-app page scanner |

### Target architecture

```
 Phone app (Capacitor) ─┐
 PWA / mobile browser ──┼── HTTPS ──► Caddy (TLS, static frontend, reverse proxy)
 Desktop browser ───────┘                 │
                                          ▼
                              FastAPI  (app/api/*)  ── verifies login token on every request
                                │        │      │
                     Postgres ◄─┘        │      └─► Object storage (pictures, page uploads)
          users · folders · documents    │                ▲
          assets · ocr_jobs              │                │
                     ▲                   ▼                │
                     └──────── OCR worker (python -m app.worker)
                               mokuro + manga-ocr + DocLayout-YOLO, one job at a time

 Auth: Supabase Auth (email magic link) issues JWTs; the API only verifies them.
```

### Recommended building blocks

- **Supabase** for Postgres + Auth + Storage, on the free tier first. One provider covers three
  needs, it is plain Postgres underneath (no lock-in on the data), and it runs locally with
  `supabase start` for development. The API keeps owning all logic; Supabase is infrastructure.
- **Hetzner VPS** (or similar) with 16 GB RAM for the API + worker, Docker Compose, Caddy for
  automatic HTTPS. Move the worker to a GPU machine only if page times hurt.
- **A jobs table in Postgres** (`SELECT … FOR UPDATE SKIP LOCKED`) instead of Redis: one less
  service, and jobs survive restarts.
- **Capacitor** for the store apps: it wraps the same vanilla-JS frontend, no rewrite.

---

## Phase 0 — Groundwork (no user-visible change)

Goal: the app is configured by environment, runs in containers, and is tested on every push.

1. **Settings from the environment.** `backend/app/config.py` becomes a `pydantic-settings`
   `Settings` class: `DATABASE_URL`, `STORAGE_*`, `AUTH_JWT_*`, `ALLOWED_ORIGINS`,
   `OCR_DAILY_QUOTA`, `ENV` (`dev`/`test`/`prod`). Constants that are product rules
   (`MAX_LOOKUP_CHARS`…) stay as constants.
2. **Containers.** One `backend/Dockerfile` (uv, Python 3.12, model weights downloaded at build
   time into the image so containers start without network); `compose.yaml` with `api`,
   `worker`, `caddy`. `frontend/` is served by Caddy as static files.
3. **CI.** GitHub Actions: `ruff` + `pytest` on every push, with a Postgres service container.
   Playwright smoke tests (the drivers used during development, turned into a `tests/e2e/`
   suite) on the main branch.
4. **Licence decision** (blocking for going public, see §7): AGPL for the whole app, or swap
   DocLayout-YOLO for a permissively licensed layout model.

Done when: `docker compose up` serves the current app; CI is green.

---

## Phase 1 — Accounts and per-user data

Goal: anyone can sign in with their email and gets their own private library.

### 1.1 Database: SQLite → Postgres
- Rewrite `app/services/library.py` on **SQLAlchemy Core + psycopg**, keeping the
  `LibraryStore` method names so `app/api/library.py` barely changes. Every method gains a
  `user_id` argument and every query filters by it; a cross-user id returns `NotFoundError`
  (404), never someone else's data.
- **Alembic** migrations in `backend/migrations/`. Schema:
  - `users(id uuid pk = auth user id, email, created_at, settings jsonb)` — `settings` holds the
    Ask AI template and provider (today in localStorage).
  - `folders(id, user_id fk, name, created_at)`
  - `documents(id, user_id fk, folder_id fk on delete cascade, title, html, version int, created_at, updated_at)`
  - `assets(id uuid, user_id, document_id null, storage_key, mime, bytes, created_at)`
  - `ocr_jobs(id uuid, user_id, status, upload_key, result jsonb, error, attempts, created_at, finished_at)`
  - indexes on every `user_id` and `(folder_id)`, `(status, created_at)` for jobs.
- Tests run against Postgres (CI service / `testcontainers` locally); the existing store tests
  in `tests/test_library.py` are kept and extended with "user A can't see user B" cases.

### 1.2 Sign-in
- **Backend:** `app/api/auth.py` with a `current_user` dependency: reads the
  `Authorization: Bearer <jwt>`, verifies signature/expiry against Supabase's JWT secret or JWKS,
  upserts the `users` row on first sight, returns the user id. Applied to **every** `/api` route
  except `/api/health` — OCR and lookups cost compute, so they need a user too.
  `ENV=test` swaps in a fixed test user (dependency override, as already done for `ocr_engine`).
- **Frontend:** `frontend/js/auth/` — Supabase JS client (pinned ESM build from a CDN, no build
  step). `api.js` stays the only `fetch` site and adds the bearer token, refreshing it when
  needed. A retro **sign-in window** on the desktop: email field → "Check your email" → the magic
  link returns to the app signed in. Menu bar shows the email and **[ SIGN OUT ]**.
- **Account page** (a desktop "program"): change email, **export my library** (zip of documents
  as HTML + pictures), **delete my account** (required by the App Store; deletes rows and files).

### 1.3 Pictures out of the HTML
- OCR stops returning `data:` URIs. The worker uploads each dithered PNG to storage
  (`users/{uid}/assets/{uuid}.png`), records an `assets` row and returns `{ type: "figure",
  asset_id, width_ratio, align }`.
- Documents store `<img data-asset="…">` without a `src`. When a document opens, the API returns
  short-lived **signed URLs** for its assets and the editor fills in `src`
  (`frontend/js/screens/editor-screen.js`). Saving strips `src` again, so stored HTML never
  contains expiring links.
- A one-off migration moves existing `data:` URIs into assets.
- Effect: documents shrink from megabytes to kilobytes, which makes saving and phone use fast.

### 1.4 Two devices, one document
- `documents.version` increments on every save. `PUT /api/documents/{id}` sends the version it
  started from; if the server's is newer it answers **409**. The editor shows a retro dialog:
  "This document was changed on another device — [ LOAD THEIRS ] [ KEEP MINE ]".
- Autosave keeps today's behaviour (Edited → Saving… → Saved, leave-page warning).

### 1.5 Server-side HTML clean-up
Saved HTML is rendered back into the page, so the API sanitises it on every save with an
allow-list (**nh3**): `p h1 h2 hr div span ruby rt figure img` with only the classes and
`data-*` attributes the editor uses (`columns`, `column`, `caption`, `page-break`, `note-*`,
`figure--*`, `data-note`, `data-asset`, `style="width|flex-grow"`). Anything else is dropped.

### 1.6 Bringing the prototype's data along
`python -m app.tools.import_sqlite --email you@example.com backend/data/library.sqlite`
copies folders and documents into that account (pictures become assets).

Done when: two accounts can sign in on different browsers, each sees only their own folders,
documents round-trip with pictures, a stale save gets the 409 dialog, and account deletion
removes everything.

---

## Phase 2 — Hosting and the OCR pipeline

Goal: the site is live on a domain over HTTPS, and OCR is reliable under real use.

### 2.1 OCR as jobs
- `POST /api/ocr` stores the upload in object storage, creates an `ocr_jobs` row and returns
  **202** `{ job_id }` immediately.
- `app/worker.py` (`python -m app.worker`): loads the models once, loops claiming the oldest
  `queued` job with `FOR UPDATE SKIP LOCKED`, runs the existing pipeline
  (`app/services/ocr/service.py` is unchanged), writes `result` or `error`, retries a crashed
  job up to 2 times. The MPS/GPU lock disappears: one worker process = one job at a time.
- `GET /api/ocr/jobs/{id}` → `queued | running | done (+ items) | failed`. `frontend/js/ui/upload.js`
  polls every second with the existing text progress bar; the page is inserted on `done`.
- Upload images are deleted after 24 h.

### 2.2 Limits and abuse protection
- Per-user daily OCR quota (e.g. 100 pages), enforced when the job is created; shown in the
  status bar when close.
- Rate limits on lookups and auth endpoints (`slowapi`).
- The browser downsizes photos before upload (longest side 3000 px, JPEG ~0.85), which cuts
  12-MP phone photos from ~4 MB to ~600 KB without hurting OCR.

### 2.3 Deployment
- **Server:** 16 GB RAM VPS. `compose.yaml`: `caddy` (TLS, static frontend, proxy `/api`),
  `api` (2 uvicorn workers), `worker` (1 process). Models baked into the image.
- **CI/CD:** on a version tag, GitHub Actions builds the image, pushes it to a registry, and
  deploys over SSH (`docker compose pull && up -d`) after migrations run.
- **Environments:** `staging.<domain>` and `<domain>`, each with its own Supabase project.
- **Backups:** Supabase daily backups (paid plan) or a nightly `pg_dump` to storage; storage
  bucket versioning on. A restore is rehearsed once before launch.
- **Monitoring:** Sentry (errors, frontend + backend), an uptime check on `/api/health`, worker
  queue length and job duration logged.
- **Security headers** in Caddy: HSTS, a Content-Security-Policy that allows only our origin,
  the pinned CDN, Supabase, and `chatgpt.com`/`claude.ai` for the Ask AI window.

Done when: the site runs at its domain, a page photo goes through the queue in production,
backups exist, and errors reach Sentry.

---

## Phase 3 — Phone-ready website and installable app (PWA)

Goal: everything works comfortably on a phone, the camera opens from the app, and it installs
to the home screen.

### 3.1 Layout
- Breakpoint around 700 px, tokens in `frontend/css/tokens.css`.
- **Desktop surface on phones:** a home-screen grid of the same pixel icons; a folder opens as a
  full-screen window with a back arrow instead of a draggable one; dialogs go full width.
- **Editor on phones:** page goes edge to edge with smaller margins, the toolbar moves to a
  bottom bar (`◂ Desktop`, `Camera`, `AI Chat`), columns stack vertically, document font
  slightly smaller.

### 3.2 Touch
- **Selection:** phones select with a long press and handles; the lookup opens on
  `selectionchange` (debounced) instead of `mouseup`, as a **bottom sheet** rather than a box
  beside the word (`frontend/js/ui/lookup-popup.js`, `note-popup.js`, `ask-ai-dialog.js` share a
  `placeBeside`/`sheet` helper — `ui/place.js` grows a mobile mode).
- **Open with one tap** where desktop uses double-click (pointer type check).
- **Pictures:** tap to select; bigger resize handle; long-press-and-drag to move (the code is
  already pointer-events based).
- **Notes and furigana:** tap to open, as today's click.

### 3.3 Camera
- The upload button gets `accept="image/*" capture="environment"` on phones: one tap opens the
  rear camera; the photo goes straight into the OCR job. Multi-page: shoot, wait, shoot again —
  pages append at the cursor as they do now.
- Client-side resize before upload (§2.2).

### 3.4 Installable (PWA)
- `frontend/manifest.webmanifest` (name, mint/pink theme colours, pixel-art icons at 192/512 px,
  `display: standalone`), iOS meta tags and touch icon.
- A service worker caches the app shell (HTML/CSS/JS/icons) so it opens instantly and shows a
  friendly offline screen; API calls stay network-only for now.

### 3.5 Ask AI on phones
No floating windows on phones: Send opens ChatGPT/Claude in a new tab (or their app, if
installed); the prompt is still copied as a fallback. The full-screen notice copy adapts.

Done when: on a real iPhone and Android phone you can sign in, photograph a page, read it, look
up words, add notes and furigana, and install the app to the home screen. Playwright runs the
e2e suite with iPhone and Pixel emulation.

---

## Phase 4 — App Store and Google Play (optional)

Goal: real store apps, for people who look for apps there.

1. **Capacitor project** in `mobile/` (needs Node, Xcode, Android Studio). `webDir` points at a
   copy of `frontend/`; the API base URL becomes absolute (`https://<domain>/api`) via
   `frontend/js/config.js`; CORS allows `capacitor://localhost` and `https://localhost`.
2. **Plugins:** Camera (native capture UI), App (deep links), Preferences (session storage),
   Share (export).
3. **Magic links into the app:** universal links (iOS) / app links (Android) on `<domain>/auth/*`
   open the app and complete sign-in; email OTP codes as a fallback.
4. **Store requirements:** in-app account deletion (done in 1.2), privacy labels (email, user
   content, no tracking), screenshots, review notes with a demo account. Email-only sign-in does
   not require Sign in with Apple. The camera, offline shell and notes make it clearly more than
   a wrapped website, which matters for Apple's review.
5. **Release:** Fastlane lanes for TestFlight / internal testing, then store submission.
   Accounts: Apple Developer ($99/yr), Google Play ($25 once).

Done when: the app is approved in both stores and shares the same accounts and library as the
website.

---

## Phase 5 — Later

- **Offline reading and editing:** cache opened documents in IndexedDB, queue saves while
  offline, sync with the `version` check from 1.4.
- **Page scanner:** in-app camera view that finds page edges and straightens the photo before
  OCR (OpenCV.js on the device, or server-side) — fixes the skew problems seen on real photos.
- **Program windows on the desktop:** the writing tool and kanji tool planned earlier.
- **Contrast clean-up** for coloured highlighted text before OCR.

---

## 6. Costs (starting scale)

| Item | Monthly |
|---|---|
| VPS, 16 GB RAM (API + worker) | ~€30–60 |
| Supabase (free tier → Pro when backups matter) | $0 → $25 |
| Object storage (Cloudflare R2 or Supabase) | ~$0–5 |
| Email sending (magic links) | free tier |
| Sentry, uptime monitor | free tiers |
| Domain | ~$1 |
| Apple Developer / Google Play | $99/yr · $25 once |
| GPU worker (only if needed) | ~$100+ |

CPU-only OCR is my estimate at roughly 10–30 s per page (2–8 s on the M5 today); measure on the
chosen server in Phase 2 before deciding on a GPU.

## 7. Risks and how they're handled

| Risk | Handling |
|---|---|
| **AGPL (DocLayout-YOLO)**: serving it publicly obliges publishing the app's source under AGPL | Decide in Phase 0: open-source the app under AGPL, or replace the model with a permissively licensed layout model (evaluate e.g. PaddleOCR's layout models) |
| GPL comic-text-detector | Fine on the server; never bundle it in the phone apps (OCR stays server-side) |
| Dictionary licences (JMdict / KANJIDIC, CC BY-SA, EDRDG) | Attribution page in the app and README |
| Users photograph copyrighted books | Terms: personal study use; documents are private; no sharing feature |
| OCR cost / abuse | Login required, per-user quotas, rate limits, client-side downsizing |
| Stored HTML used for XSS | Server-side allow-list sanitising (1.5) and a strict CSP (2.3) |
| Two devices editing at once | Version check + conflict dialog (1.4) |
| Ask AI `?q=` links change | Prompt is always copied too |
| Losing data | Daily backups + a rehearsed restore; account export |

## 8. Order of work and rough size

| Phase | Rough size (one developer pairing with Claude) |
|---|---|
| 0 Groundwork | 2–3 days |
| 1 Accounts + per-user data | 1.5–2 weeks |
| 2 Hosting + OCR jobs | ~1 week |
| 3 Phone-ready + PWA + camera | 1.5–2 weeks |
| 4 Store apps | ~1 week of work, plus store review time |

These are planning estimates, not measurements; Phase 1 and 3 carry the most uncertainty.

## 9. Decisions needed from you

1. **Licence:** open-source the app (AGPL) **or** replace DocLayout-YOLO. *Default: replace it,
   unless open-sourcing appeals.*
2. **Auth/data provider:** Supabase **or** fully self-hosted (Postgres + MinIO + own magic-link
   emails). *Default: Supabase.*
3. **Server:** Hetzner (EU, cheapest) or a managed platform (Fly.io / Render, simpler, pricier).
   *Default: Hetzner.*
4. **Name and domain** for the public site.
5. **Store apps:** needed at launch, or PWA first? *Default: PWA first, stores in Phase 4.*
6. **Budget ceiling** for compute, which decides CPU vs GPU OCR.
