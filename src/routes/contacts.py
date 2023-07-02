from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status, Query
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User, Role
from src.schemas import ContactResponse, ContactModel
from src.repository import contacts as repository_contacts
from src.services.auth import auth_service
from src.services.roles import RolesAccess

router = APIRouter(prefix="/contacts", tags=["contacts"])

access_get = RolesAccess([Role.admin, Role.moderator, Role.user])
access_create = RolesAccess([Role.admin, Role.moderator])
access_update = RolesAccess([Role.admin, Role.moderator])
access_delete = RolesAccess([Role.admin])


@router.get("/", response_model=List[ContactResponse],
            dependencies=[Depends(access_get)],
            name='Get a list of contacts using query parameters: first name, last name, email')
async def get_contacts(limit: int = Query(default=10),
                       offset: int = 0,
                       first_name: Optional[str] = Query(default=None),
                       last_name: Optional[str] = Query(default=None),
                       email: Optional[str] = Query(default=None),
                       db: Session = Depends(get_db),
                       _: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.get_contacts(limit, offset, first_name, last_name, email, db)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Contacts with requested parameters not found")
    return contact


@router.get("/birthdays", response_model=List[ContactResponse],
            dependencies=[Depends(access_get)],
            name='Get a list of all contacts who has birthday during next 7 days')
async def get_contacts_by_birthday(limit: int = Query(10, le=300), offset: int = 0,
                                   db: Session = Depends(get_db),
                                   _: User = Depends(auth_service.get_current_user)):
    contacts = await repository_contacts.search_contacts_by_birthday(limit, offset, db)
    if not contacts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found!")
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse,
            dependencies=[Depends(access_get)])
async def get_contact(contact_id: int = Path(ge=1),
                      db: Session = Depends(get_db),
                      _: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.get_contact_by_id(contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found!")
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(access_create)])
async def create_contact(body: ContactModel,
                         db: Session = Depends(get_db),
                         _: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.create(body, db)
    return contact


@router.put("/{contact_id}", response_model=ContactResponse,
            dependencies=[Depends(access_update)])
async def update_contact(body: ContactModel, contact_id: int = Path(ge=1),
                         db: Session = Depends(get_db),
                         _: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.update(contact_id, body, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found!")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(access_delete)])
async def delete_contact(contact_id: int = Path(ge=1),
                         db: Session = Depends(get_db),
                         _: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.remove(contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found!")
    return None
