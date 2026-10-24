# 0007 — Library: folders of documents in SQLite, behind a desktop

**Status:** accepted · 2026-10-24

## Context
The app held a single document in the browser's localStorage. The user wants a learning library
(a folder per book, one for pamphlets, more tools later) opened from a retro desktop. Pictures
are stored inside documents as data URIs, which would soon exceed the ~5 MB browser quota.

## Decision
- **Storage:** one SQLite file, `backend/data/library.sqlite`, via the standard library
  (`services/library.py`). Two tables: `folders` and `documents` (title + the editor's HTML),
  with documents deleted together with their folder. `PRAGMA user_version` marks the schema for
  future migrations. One short-lived connection per operation, so it's safe from FastAPI's
  thread pool. No ORM: two tables don't need one.
- **Shape:** folders are one level deep; a book is a folder with one document per chapter or
  reading session. A pamphlet is a document in a "Pamphlets" folder.
- **API:** `/api/folders` and `/api/documents` (`api/library.py`), the store injected so tests
  use a temporary database.
- **Frontend:** a hash router (`#/`, `#/folder/<id>`, `#/doc/<id>`) switches between the desktop
  and the unchanged editor. The editor autosaves through a callback (`onSave`) instead of owning
  storage. The old localStorage document is moved into an "Imported" folder once.

## Consequences
- Documents are no longer tied to one browser profile and have no practical size limit.
- Backing up means copying one file. A future sync or multi-device setup would start here.
- Whole-document saves: fine for chapters and pamphlets; a whole novel in one document would
  save slowly, which is why books are folders of documents.
