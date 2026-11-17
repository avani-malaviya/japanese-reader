from dataclasses import asdict
from functools import cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from app.api.schemas import (
    DocumentContentIn,
    DocumentIn,
    DocumentOut,
    DocumentPatch,
    DocumentSummaryOut,
    FolderIn,
    FolderOut,
)
from app.config import get_settings
from app.services.library import LibraryStore, NotFoundError

router = APIRouter()


@cache
def library_store() -> LibraryStore:
    return LibraryStore(get_settings().library_db)


Store = Annotated[LibraryStore, Depends(library_store)]


def not_found_handler(_request: Request, error: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(error)})


# ---- folders ----


@router.get("/folders", response_model=list[FolderOut])
def list_folders(store: Store) -> list[FolderOut]:
    return [FolderOut(**asdict(f)) for f in store.list_folders()]


@router.post("/folders", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
def create_folder(body: FolderIn, store: Store) -> FolderOut:
    return FolderOut(**asdict(store.create_folder(body.name)))


@router.patch("/folders/{folder_id}", response_model=FolderOut)
def rename_folder(folder_id: int, body: FolderIn, store: Store) -> FolderOut:
    return FolderOut(**asdict(store.rename_folder(folder_id, body.name)))


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(folder_id: int, store: Store) -> Response:
    store.delete_folder(folder_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---- documents ----


@router.get("/folders/{folder_id}/documents", response_model=list[DocumentSummaryOut])
def list_documents(folder_id: int, store: Store) -> list[DocumentSummaryOut]:
    return [DocumentSummaryOut(**asdict(d)) for d in store.list_documents(folder_id)]


@router.post(
    "/folders/{folder_id}/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED
)
def create_document(folder_id: int, body: DocumentIn, store: Store) -> DocumentOut:
    return DocumentOut(**asdict(store.create_document(folder_id, body.title)))


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, store: Store) -> DocumentOut:
    return DocumentOut(**asdict(store.get_document(document_id)))


@router.put("/documents/{document_id}", response_model=DocumentSummaryOut)
def save_document(document_id: int, body: DocumentContentIn, store: Store) -> DocumentSummaryOut:
    return DocumentSummaryOut(**asdict(store.save_html(document_id, body.html)))


@router.patch("/documents/{document_id}", response_model=DocumentSummaryOut)
def update_document(document_id: int, body: DocumentPatch, store: Store) -> DocumentSummaryOut:
    if body.title is None and body.folder_id is None:
        raise HTTPException(status_code=422, detail="Nothing to change")
    updated = store.update_document(document_id, title=body.title, folder_id=body.folder_id)
    return DocumentSummaryOut(**asdict(updated))


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, store: Store) -> Response:
    store.delete_document(document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
