from pathlib import Path

import pytest

from app.services.library import LibraryStore, NotFoundError


@pytest.fixture
def store(tmp_path: Path) -> LibraryStore:
    return LibraryStore(tmp_path / "library.sqlite")


def test_folders_hold_documents(store: LibraryStore) -> None:
    pamphlets = store.create_folder("Pamphlets")
    book = store.create_folder("ノルウェイの森")
    store.create_document(pamphlets.id, "Zoo leaflet")
    store.create_document(pamphlets.id, "Bus timetable")

    counts = {f.name: f.document_count for f in store.list_folders()}
    assert counts == {"Pamphlets": 2, "ノルウェイの森": 0}
    assert [d.title for d in store.list_documents(pamphlets.id)] == ["Bus timetable", "Zoo leaflet"]
    assert store.list_documents(book.id) == []


def test_document_html_round_trip(store: LibraryStore) -> None:
    folder = store.create_folder("Book")
    document = store.create_document(folder.id, "Chapter 1")
    assert document.html == ""
    html = '<h1>第一章</h1><p><ruby>日本<rt contenteditable="false">にほん</rt></ruby></p>'
    store.save_html(document.id, html)
    assert store.get_document(document.id).html == html


def test_rename_and_move(store: LibraryStore) -> None:
    inbox, book = store.create_folder("Inbox"), store.create_folder("Book")
    document = store.create_document(inbox.id, "untitled")
    store.update_document(document.id, title="Chapter 2", folder_id=book.id)
    moved = store.get_document(document.id)
    assert (moved.title, moved.folder_id) == ("Chapter 2", book.id)
    assert store.rename_folder(book.id, "Kokoro").name == "Kokoro"


def test_deleting_a_folder_deletes_its_documents(store: LibraryStore) -> None:
    folder = store.create_folder("Pamphlets")
    document = store.create_document(folder.id, "Zoo leaflet")
    store.delete_folder(folder.id)
    assert store.list_folders() == []
    with pytest.raises(NotFoundError):
        store.get_document(document.id)


def test_unknown_ids_raise(store: LibraryStore) -> None:
    with pytest.raises(NotFoundError):
        store.list_documents(99)
    with pytest.raises(NotFoundError):
        store.create_document(99, "x")
    with pytest.raises(NotFoundError):
        store.save_html(99, "")
    with pytest.raises(NotFoundError):
        store.delete_folder(99)


def test_data_survives_reopening(tmp_path: Path) -> None:
    path = tmp_path / "library.sqlite"
    folder = LibraryStore(path).create_folder("Pamphlets")
    assert [f.id for f in LibraryStore(path).list_folders()] == [folder.id]
