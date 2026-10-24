"""The library: folders (a book, "Pamphlets", ...) holding documents (a chapter, a pamphlet).

Stored in one SQLite file. A document's content is the editor's HTML, pictures included.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

SCHEMA_VERSION = 1
SCHEMA = """
CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    folder_id INTEGER NOT NULL REFERENCES folders(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    html TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS documents_by_folder ON documents(folder_id);
"""


class NotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class Folder:
    id: int
    name: str
    created_at: str
    document_count: int
    updated_at: str  # latest change to the folder or any of its documents


@dataclass(frozen=True)
class DocumentSummary:
    id: int
    folder_id: int
    title: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class Document(DocumentSummary):
    html: str


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class LibraryStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(SCHEMA)
            db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    # One short-lived connection per operation: safe from FastAPI's worker threads.
    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            with db:  # commits, or rolls back on error
                yield db
        finally:
            db.close()

    # ---- folders ----

    def list_folders(self) -> list[Folder]:
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT f.id, f.name, f.created_at,
                       COUNT(d.id) AS document_count,
                       MAX(f.created_at, COALESCE(MAX(d.updated_at), '')) AS updated_at
                FROM folders f LEFT JOIN documents d ON d.folder_id = f.id
                GROUP BY f.id ORDER BY f.name COLLATE NOCASE, f.id
                """
            ).fetchall()
        return [Folder(**row) for row in rows]

    def get_folder(self, folder_id: int) -> Folder:
        folder = next((f for f in self.list_folders() if f.id == folder_id), None)
        if folder is None:
            raise NotFoundError(f"No folder {folder_id}")
        return folder

    def create_folder(self, name: str) -> Folder:
        with self._connect() as db:
            folder_id = db.execute(
                "INSERT INTO folders (name, created_at) VALUES (?, ?)", (name, _now())
            ).lastrowid
        return self.get_folder(folder_id)

    def rename_folder(self, folder_id: int, name: str) -> Folder:
        with self._connect() as db:
            if not db.execute("UPDATE folders SET name = ? WHERE id = ?", (name, folder_id)).rowcount:
                raise NotFoundError(f"No folder {folder_id}")
        return self.get_folder(folder_id)

    def delete_folder(self, folder_id: int) -> None:
        """Deletes the folder and every document in it."""
        with self._connect() as db:
            if not db.execute("DELETE FROM folders WHERE id = ?", (folder_id,)).rowcount:
                raise NotFoundError(f"No folder {folder_id}")

    # ---- documents ----

    def list_documents(self, folder_id: int) -> list[DocumentSummary]:
        self.get_folder(folder_id)
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT id, folder_id, title, created_at, updated_at FROM documents
                WHERE folder_id = ? ORDER BY title COLLATE NOCASE, id
                """,
                (folder_id,),
            ).fetchall()
        return [DocumentSummary(**row) for row in rows]

    def create_document(self, folder_id: int, title: str, html: str = "") -> Document:
        self.get_folder(folder_id)
        now = _now()
        with self._connect() as db:
            document_id = db.execute(
                """
                INSERT INTO documents (folder_id, title, html, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (folder_id, title, html, now, now),
            ).lastrowid
        return self.get_document(document_id)

    def get_document(self, document_id: int) -> Document:
        with self._connect() as db:
            row = db.execute(
                "SELECT id, folder_id, title, created_at, updated_at, html FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError(f"No document {document_id}")
        return Document(**row)

    def save_html(self, document_id: int, html: str) -> DocumentSummary:
        return self._update(document_id, html=html)

    def update_document(
        self, document_id: int, *, title: str | None = None, folder_id: int | None = None
    ) -> DocumentSummary:
        """Renames the document and/or moves it to another folder."""
        if folder_id is not None:
            self.get_folder(folder_id)
        return self._update(document_id, title=title, folder_id=folder_id)

    def delete_document(self, document_id: int) -> None:
        with self._connect() as db:
            if not db.execute("DELETE FROM documents WHERE id = ?", (document_id,)).rowcount:
                raise NotFoundError(f"No document {document_id}")

    def _update(self, document_id: int, **fields: object) -> DocumentSummary:
        changes = {key: value for key, value in fields.items() if value is not None}
        changes["updated_at"] = _now()
        assignments = ", ".join(f"{column} = ?" for column in changes)
        with self._connect() as db:
            updated = db.execute(
                f"UPDATE documents SET {assignments} WHERE id = ?", (*changes.values(), document_id)
            ).rowcount
        if not updated:
            raise NotFoundError(f"No document {document_id}")
        document = self.get_document(document_id)
        return DocumentSummary(
            document.id, document.folder_id, document.title, document.created_at, document.updated_at
        )
