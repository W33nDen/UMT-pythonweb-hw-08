from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Contact
from app.schemas import ContactCreate, ContactUpdate


def get_contacts(
    db: Session,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
) -> list[Contact]:
    query = select(Contact).order_by(Contact.id)

    if first_name:
        query = query.where(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.where(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        query = query.where(Contact.email.ilike(f"%{email}%"))

    return list(db.scalars(query).all())


def get_contact(db: Session, contact_id: int) -> Contact | None:
    return db.get(Contact, contact_id)


def get_contact_by_email(db: Session, email: str) -> Contact | None:
    return db.scalar(select(Contact).where(Contact.email == email))


def create_contact(db: Session, contact: ContactCreate) -> Contact:
    db_contact = Contact(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def update_contact(db: Session, db_contact: Contact, contact: ContactUpdate) -> Contact:
    update_data = contact.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_contact, field, value)

    db.commit()
    db.refresh(db_contact)
    return db_contact


def delete_contact(db: Session, db_contact: Contact) -> Contact:
    db.delete(db_contact)
    db.commit()
    return db_contact


def _next_birthday(birthday: date, today: date) -> date:
    try:
        next_birthday = birthday.replace(year=today.year)
    except ValueError:
        next_birthday = date(today.year, 3, 1)

    if next_birthday < today:
        try:
            next_birthday = birthday.replace(year=today.year + 1)
        except ValueError:
            next_birthday = date(today.year + 1, 3, 1)

    return next_birthday


def get_upcoming_birthdays(db: Session, days: int = 7) -> list[Contact]:
    today = date.today()
    end_date = today + timedelta(days=days)
    contacts = db.scalars(select(Contact).order_by(Contact.id)).all()

    return [
        contact
        for contact in contacts
        if today <= _next_birthday(contact.birthday, today) <= end_date
    ]

