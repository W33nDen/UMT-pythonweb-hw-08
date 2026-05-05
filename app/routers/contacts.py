from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import ContactCreate, ContactResponse, ContactUpdate


router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)) -> ContactResponse:
    if crud.get_contact_by_email(db, contact.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with this email already exists",
        )

    return crud.create_contact(db, contact)


@router.get("/", response_model=list[ContactResponse])
def read_contacts(
    first_name: str | None = Query(default=None, description="Search by first name"),
    last_name: str | None = Query(default=None, description="Search by last name"),
    email: str | None = Query(default=None, description="Search by email"),
    db: Session = Depends(get_db),
) -> list[ContactResponse]:
    return crud.get_contacts(db, first_name=first_name, last_name=last_name, email=email)


@router.get("/birthdays/upcoming", response_model=list[ContactResponse])
def read_upcoming_birthdays(db: Session = Depends(get_db)) -> list[ContactResponse]:
    return crud.get_upcoming_birthdays(db)


@router.get("/{contact_id}", response_model=ContactResponse)
def read_contact(contact_id: int, db: Session = Depends(get_db)) -> ContactResponse:
    contact = crud.get_contact(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    contact_update: ContactUpdate,
    db: Session = Depends(get_db),
) -> ContactResponse:
    contact = crud.get_contact(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    if contact_update.email and contact_update.email != contact.email:
        existing_contact = crud.get_contact_by_email(db, contact_update.email)
        if existing_contact:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Contact with this email already exists",
            )

    return crud.update_contact(db, contact, contact_update)


@router.delete("/{contact_id}", response_model=ContactResponse)
def delete_contact(contact_id: int, db: Session = Depends(get_db)) -> ContactResponse:
    contact = crud.get_contact(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    return crud.delete_contact(db, contact)

