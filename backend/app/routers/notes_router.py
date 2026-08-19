from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.note_schema import NoteCreate, NoteRead, NoteUpdate
from app.services.notes_service import create_note, delete_note, get_note_for_user, list_user_notes, update_note

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=list[NoteRead])
def list_notes(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return list_user_notes(session, current_user.id)


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_note_route(
    payload: NoteCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return create_note(session, current_user.id, payload.title, payload.content)


@router.get("/{note_id}", response_model=NoteRead)
def read_note(note_id: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return get_note_for_user(session, note_id, current_user.id)


@router.put("/{note_id}", response_model=NoteRead)
def update_note_route(
    note_id: str,
    payload: NoteUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return update_note(session, note_id, current_user.id, payload.title, payload.content)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note_route(
    note_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    delete_note(session, note_id, current_user.id)
    return None
