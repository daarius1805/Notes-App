# Notes App + RAG Bot — Architecture & Build Plan

**Goal:** A notes app with a clean UI where you can ask a chatbot questions and it answers
using *only* the content of your own notes (Retrieval-Augmented Generation, powered by
Gemini). Built one working layer at a time.

---

## 1. What "RAG" actually means here (read this before building)

A plain chatbot only knows what it was trained on. A **RAG bot** answers using *your*
private data by doing this on every question:

1. Turn the user's question into a vector (a list of numbers representing its meaning) —
   this is called an **embedding**.
2. Search your notes' pre-computed embeddings for the ones closest in meaning to the
   question (**vector similarity search**).
3. Take the top few matching note snippets and stuff them into the prompt as context.
4. Ask Gemini to answer the question *using only that context*.

So there are really two pipelines in this app:
- **Indexing pipeline** (runs when a note is created/updated): chunk note → embed each
  chunk → store the vectors.
- **Query pipeline** (runs when the user asks the bot something): embed the question →
  find closest chunks → build a prompt → call Gemini → return the answer + which notes it
  came from.

You will build these manually (not via a heavy framework like LangChain) so you actually
learn the mechanics. Once it works, refactoring to LangChain later is easy and optional.

---

## 2. Tech stack

You asked for the AI code in Python. Rather than splitting the backend across two
languages (which mostly adds plumbing, not learning), the **whole backend is Python** —
the RAG pipeline needs direct access to the same note data the CRUD API manages, so
keeping them in one service is simpler for a first build. Frontend stays TypeScript, since
React's ecosystem is strongest there.

| Layer | Choice | Why |
|---|---|---|
| Backend language | **Python** | Your preference, and Python's AI/data ecosystem is the most mature |
| Backend framework | **FastAPI** | Async, type-hinted, auto-generates interactive API docs — great for learning |
| ORM | **SQLModel** | Combines SQLAlchemy + Pydantic, less boilerplate than raw SQLAlchemy |
| Migrations | **Alembic** | Standard migration tool paired with SQLAlchemy/SQLModel |
| Database | **PostgreSQL + pgvector extension** | One database for both your notes *and* their embeddings — no separate vector DB to run |
| Auth | **JWT + passlib(bcrypt)** | Simple to reason about, no external provider |
| AI provider | **Gemini API** (your key) | Chat generation + embeddings, via Google's official SDK |
| Frontend framework | **React + Vite + TypeScript** | Standard, well documented |
| Styling | **Tailwind CSS** | Fast to build a clean, consistent UI with |
| Rich text editor | **TipTap** | Clean editing experience, easy to strip to plain text for embedding |
| Data fetching | **TanStack Query (React Query)** | Proper async/cache handling instead of manual `useEffect` fetching |
| Client state | **Zustand** | Lightweight — for auth/theme state |
| Forms | **React Hook Form + Zod** | Schema-based validation, mirrors backend validation |

**Languages used:** Python (backend + AI), TypeScript (frontend), SQL (via
SQLModel/Alembic migrations, plus one raw vector-similarity query).

### A note on Gemini model names
Google ships new Gemini model versions frequently, and old ones get deprecated on a
schedule — the exact model string you should use **will likely have changed by the time
you build this**. Don't hardcode a model name from this doc without checking
[ai.google.dev/gemini-api/docs/models](https://ai.google.dev/gemini-api/docs/models) first.
As of today (Aug 2026), reasonable defaults are:
- **Chat/generation:** `gemini-3.5-flash-lite` (cheap, fast, GA) — step up to
  `gemini-3.6-flash` if you want stronger answers and don't mind the cost.
- **Embeddings:** `gemini-embedding-001` (GA, stable). A newer `gemini-embedding-2` may
  also be available by the time you build — worth a quick check.

Store whichever model names you pick in `.env`, not hardcoded in code, so swapping models
later is a one-line change.

---

## 3. Full project structure

```
notes-rag-app/
├── backend/                              # Python / FastAPI
│   ├── app/
│   │   ├── main.py                       # FastAPI app instance, mounts routers
│   │   ├── config.py                     # Settings via pydantic-settings (.env loader)
│   │   ├── database.py                   # SQLModel engine + session dependency
│   │   ├── dependencies.py               # get_current_user, get_session
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── note.py
│   │   │   └── note_chunk.py             # stores chunk text + embedding vector
│   │   ├── schemas/                      # Pydantic request/response shapes
│   │   │   ├── auth_schema.py
│   │   │   ├── note_schema.py
│   │   │   └── chat_schema.py
│   │   ├── routers/
│   │   │   ├── auth_router.py
│   │   │   ├── notes_router.py
│   │   │   └── chat_router.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── notes_service.py
│   │   │   ├── chunking_service.py       # splits note content into chunks
│   │   │   ├── embedding_service.py      # calls Gemini embed_content
│   │   │   ├── retrieval_service.py      # vector similarity search
│   │   │   └── rag_service.py            # orchestrates retrieval + generation
│   │   └── auth/
│   │       ├── jwt_handler.py
│   │       └── password_handler.py
│   ├── alembic/
│   │   └── versions/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                             # TypeScript / React
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── auth.api.ts
│   │   │   ├── notes.api.ts
│   │   │   └── chat.api.ts
│   │   ├── components/
│   │   │   ├── NoteEditor/NoteEditor.tsx
│   │   │   ├── NoteList/NoteList.tsx
│   │   │   ├── NoteCard/NoteCard.tsx     # shows formatted created/updated timestamp
│   │   │   ├── ChatBot/
│   │   │   │   ├── ChatPanel.tsx         # slide-out chat drawer
│   │   │   │   ├── ChatMessage.tsx       # renders answer + source note citations
│   │   │   │   └── ChatInput.tsx
│   │   │   └── Sidebar/Sidebar.tsx
│   │   ├── pages/
│   │   │   ├── AllNotesPage.tsx
│   │   │   ├── NoteDetailPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   └── RegisterPage.tsx
│   │   ├── hooks/
│   │   │   ├── useNotes.ts
│   │   │   └── useChat.ts
│   │   ├── store/
│   │   │   ├── authStore.ts
│   │   │   └── chatStore.ts              # open/closed state, message history
│   │   ├── types/
│   │   │   ├── note.types.ts
│   │   │   └── chat.types.ts
│   │   ├── utils/
│   │   │   └── formatDate.ts             # created/updated → readable date/time
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
└── docs/
    └── ARCHITECTURE.md                   # this file
```

---

## 4. Database schema

```
User
 - id (uuid, pk)
 - email (unique)
 - passwordHash
 - createdAt

Note
 - id (uuid, pk)
 - userId (fk -> User)
 - title
 - content            # HTML/markdown from TipTap
 - createdAt
 - updatedAt

NoteChunk
 - id (uuid, pk)
 - noteId (fk -> Note)
 - chunkIndex          # order within the note
 - chunkText            # plain-text slice of the note (stripped of markup)
 - embedding (vector(N))   # N = your chosen Gemini embedding model's dimension
 - createdAt
```

Why a separate `NoteChunk` table instead of embedding the whole note as one vector?
Notes can be long, and embedding models work best on smaller passages. Chunking also
lets the bot cite *which part* of which note it used — much better than "somewhere in
one of your notes."

---

## 5. Build phases

### Phase 0 — Scaffolding
**What:** Two projects running side by side, nothing connected.
**Files:** `backend/app/main.py` (bare FastAPI app returning `{"status": "ok"}`),
`frontend/` via `npm create vite@latest frontend -- --template react-ts`.
**Done when:** `uvicorn app.main:app --reload` serves on `localhost:8000`, and the Vite
dev server shows the default page.

### Phase 1 — Database + pgvector + User model
**What:** Install Postgres locally, enable the `vector` extension, define `User`,
run your first Alembic migration.
**Files:** `backend/app/database.py`, `app/models/user.py`, `alembic/versions/0001_*.py`
**Done when:** `psql` (or a GUI like TablePlus) shows a `user` table, and `CREATE
EXTENSION vector;` has succeeded on your database.
**Learning:** what an ORM/migration tool does, what a Postgres extension is.

### Phase 2 — Auth
**What:** Register/login with JWT.
**Files:** `app/auth/password_handler.py`, `jwt_handler.py`, `schemas/auth_schema.py`,
`services/auth_service.py`, `routers/auth_router.py`, `app/dependencies.py`
**Done when:** via FastAPI's auto-generated docs at `/docs`, you can register, log in,
get a token, and a protected test route rejects requests without it.
**Learning:** password hashing, JWT, FastAPI dependency injection (this is FastAPI's
signature pattern and worth understanding well).

### Phase 3 — Notes CRUD (backend only)
**What:** Full CRUD, scoped to the logged-in user, with `createdAt`/`updatedAt` set
automatically by the database.
**Files:** `app/models/note.py`, `schemas/note_schema.py`, `services/notes_service.py`,
`routers/notes_router.py`
**Done when:** you can create/read/update/delete notes via `/docs`, and one user can never
touch another's notes (test this deliberately with two accounts).
**Learning:** REST conventions, ownership checks, timestamp defaults in SQLModel.

### Phase 4 — Frontend foundation
**What:** Login/register pages, a plain note list connected to the real API.
**Files:** `api/client.ts`, `auth.api.ts`, `notes.api.ts`, `store/authStore.ts`,
`pages/LoginPage.tsx`, `RegisterPage.tsx`, `AllNotesPage.tsx`,
`components/NoteList/NoteList.tsx`, `NoteCard/NoteCard.tsx`, `hooks/useNotes.ts`
**Done when:** you can register, log in, and see your real notes listed — ugly styling is
fine here.
**Learning:** React Query basics, protected routes.

### Phase 5 — Note editor + clean note detail view
**What:** TipTap-based editor, note detail/edit page, and the **timestamp display** —
each note card and detail view shows a readable created date/time (and "edited" time if
different).
**Files:** `components/NoteEditor/NoteEditor.tsx`, `pages/NoteDetailPage.tsx`,
`utils/formatDate.ts`
**Done when:** you can write formatted notes, save them, and see "Created Aug 10, 2026,
3:41 PM" (or similar) on each note.
**Learning:** rich text editor integration, date formatting/timezones.

### Phase 6 — Chunking + embedding pipeline (this is the first real AI phase)
**What:** When a note is created or updated, split its plain-text content into chunks
and embed each chunk via Gemini, storing the vectors in `NoteChunk`.
**Files:** `services/chunking_service.py` (simple approach: split by paragraph, or fixed
token/character windows with slight overlap), `services/embedding_service.py` (wraps
`google-genai`'s `embed_content`), wire both into `notes_service.py` so saving a note
triggers re-chunking + re-embedding.
**Done when:** after saving a note, you can query the `note_chunk` table directly and see
rows with real vectors in them.
**Learning:** text chunking strategy, what an embedding actually is (print one out and
look at it — it's just a list of ~768+ floats).

### Phase 7 — Retrieval
**What:** Given a question, embed it and run a similarity search against your chunks
(cosine distance, using pgvector's `<=>` operator), scoped to the logged-in user.
**Files:** `services/retrieval_service.py`
**Done when:** a small test script that embeds a hardcoded question returns the chunks
you'd expect from your own notes, ranked by relevance.
**Learning:** vector similarity search, why this is *search*, not magic.

### Phase 8 — Generation (completing the RAG loop)
**What:** Combine retrieved chunks into a prompt (instruct Gemini to answer *only* from
the provided context, and say so if the answer isn't in it), call Gemini's chat model,
return the answer plus which notes it drew from.
**Files:** `services/rag_service.py`, `schemas/chat_schema.py`, `routers/chat_router.py`
(`POST /chat` — takes a question, returns an answer + source note references)
**Done when:** via `/docs`, asking a question about something you actually wrote in a
note returns a correct answer citing that note — and asking something unrelated to your
notes gets an honest "I don't have that in your notes" instead of a made-up answer.
**Learning:** prompt construction, grounding/instruction-following, why RAG reduces (but
doesn't eliminate) hallucination.

### Phase 9 — Chat UI
**What:** A chat panel in the frontend — ask questions, see streaming or simple
request/response answers, see which notes were cited (link back to the note).
**Files:** `components/ChatBot/ChatPanel.tsx`, `ChatMessage.tsx`, `ChatInput.tsx`,
`hooks/useChat.ts`, `store/chatStore.ts`, `api/chat.api.ts`
**Done when:** you can open the chat panel from anywhere in the app, ask a real question,
and get an answer with clickable source notes.
**Learning:** chat UI state management, loading/error states for a slower AI-backed
endpoint (these take longer than normal CRUD calls — handle that gracefully).

### Phase 10 — Clean UI polish pass
**What:** Go back through every screen with fresh eyes — consistent spacing, a real empty
state ("no notes yet — create your first one"), loading skeletons instead of blank
screens, consistent Tailwind color tokens instead of ad-hoc classes.
**Done when:** the app feels like one coherent product, not a collection of separately
built screens.

---

## 6. Optional extensions (from the earlier, fuller spec — add later if you want)

These aren't required for "notes + RAG bot," but are natural next steps once the above is
solid: tags (many-to-many), archive/unarchive, non-AI keyword search, auto-save with
debouncing, note version history, sharing with permissions. Each of these was scoped in
detail in the previous planning doc if you want to fold them in later.

---

## 7. Full package/module list

**Backend (Python)** — `backend/requirements.txt`
```
fastapi
uvicorn[standard]
sqlmodel
psycopg[binary]
pgvector
alembic
pydantic-settings
python-jose[cryptography]
passlib[bcrypt]
python-dotenv
google-genai
python-multipart
```

**Frontend (TypeScript)** — via `npm install`
```
react
react-dom
react-router-dom
@tanstack/react-query
zustand
axios
react-hook-form
zod
@hookform/resolvers
@tiptap/react
@tiptap/starter-kit
date-fns          # optional — nicer relative timestamps ("2 hours ago")
lucide-react       # optional — icon set for a clean UI
-- dev dependencies --
typescript
vite
tailwindcss
```

**Infrastructure**
- PostgreSQL (with the `pgvector` extension enabled)
- A `.env` file (never committed) holding `DATABASE_URL`, `JWT_SECRET`, and
  `GEMINI_API_KEY`

---

## 8. API reference (target state)

| Method | Route | Purpose | Phase |
|---|---|---|---|
| POST | `/auth/register` | Create account | 2 |
| POST | `/auth/login` | Get JWT | 2 |
| GET | `/notes` | List user's notes | 3 |
| POST | `/notes` | Create note (triggers chunk+embed) | 3, 6 |
| GET | `/notes/:id` | Get one note | 3 |
| PUT | `/notes/:id` | Update note (re-chunks+re-embeds) | 3, 6 |
| DELETE | `/notes/:id` | Delete note (cascades to chunks) | 3 |
| POST | `/chat` | Ask the RAG bot a question | 8 |

---

## 9. Consistency check (reviewed)

- ✅ Notes app with clean UI, created date/time shown — Phases 4–5, 10.
- ✅ RAG bot answering from notes, using Gemini API key — Phases 6–9, the core of this doc.
- ✅ AI code in Python — entire backend, including the RAG pipeline, is Python; only the
  UI layer is TypeScript, which is unavoidable for a real React frontend.
- ✅ Every phase builds on a completed previous one: auth (2) before notes (3), notes (3)
  before chunking (6) since chunks depend on note content existing, chunking (6) before
  retrieval (7), retrieval (7) before generation (8), generation (8) before the chat UI (9).
- ✅ Package list matches every service file referenced in the phases — no phase calls a
  library that isn't listed in Section 7.
- One judgment call worth flagging: chunking and embedding happen as **part of the note
  save request** (synchronous) rather than in a background job/queue. That's the right
  choice for a learning project — background task queues (Celery, etc.) are a real
  addition to production RAG systems, but they're a separate concept worth learning on
  their own later, not bundled into your first RAG build.
- Gemini model names are called out explicitly as something to re-verify at build time
  rather than trusted from this document, since they change faster than this plan will
  stay accurate.