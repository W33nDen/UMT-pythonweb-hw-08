from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Contact, User
from app.schemas import ContactCreate, ContactUpdate, UserCreate
from app.auth import get_password_hash


# User Operations
def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    # Generate default Gravatar avatar based on email or empty
    avatar_url = f"https://www.gravatar.com/avatar/{hash(user.email)}?d=identicon"
    db_user = User(
        email=user.email,
        password=hashed_password,
        avatar=avatar_url,
        is_verified=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def verify_user(db: Session, email: str) -> None:
    db_user = get_user_by_email(db, email)
    if db_user:
        db_user.is_verified = True
        db.commit()


def update_user_avatar(db: Session, user_id: int, avatar_url: str) -> User | None:
    db_user = db.get(User, user_id)
    if db_user:
        db_user.avatar = avatar_url
        db.commit()
        db.refresh(db_user)
    return db_user


# Contact Operations
def get_contacts(
    db: Session,
    user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
) -> list[Contact]:
    query = select(Contact).where(Contact.user_id == user_id).order_by(Contact.id)

    if first_name:
        query = query.where(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.where(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        query = query.where(Contact.email.ilike(f"%{email}%"))

    return list(db.scalars(query).all())


def get_contact(db: Session, contact_id: int, user_id: int) -> Contact | None:
    return db.scalar(select(Contact).where(Contact.id == contact_id, Contact.user_id == user_id))


def get_contact_by_email(db: Session, email: str, user_id: int) -> Contact | None:
    return db.scalar(select(Contact).where(Contact.email == email, Contact.user_id == user_id))


def create_contact(db: Session, contact: ContactCreate, user_id: int) -> Contact:
    db_contact = Contact(**contact.model_dump(), user_id=user_id)
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


def get_upcoming_birthdays(db: Session, user_id: int, days: int = 7) -> list[Contact]:
    today = date.today()
    end_date = today + timedelta(days=days)
    contacts = db.scalars(select(Contact).where(Contact.user_id == user_id).order_by(Contact.id)).all()

    return [
        contact
        for contact in contacts
        if today <= _next_birthday(contact.birthday, today) <= end_date
    ]
