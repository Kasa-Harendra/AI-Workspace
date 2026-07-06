from unicodedata import category
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import Integer, String, ForeignKey

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    
    google_accounts: Mapped[list["GoogleAccount"]] = relationship("GoogleAccount", back_populates="user", cascade="all, delete-orphan")

class GoogleAccount(Base):
    __tablename__ = "google_accounts"
    
    google_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String, nullable=False)
    
    user: Mapped["User"] = relationship("User", back_populates="google_accounts")
    mails: Mapped[list["Mail"]] = relationship("Mail", back_populates="google_account", cascade="all, delete-orphan")

class Mail(Base):
    __tablename__ = "mails"
    
    mail_id: Mapped[str] = mapped_column(String, primary_key=True)
    google_id: Mapped[str] = mapped_column(String, ForeignKey("google_accounts.google_id", ondelete="CASCADE"), primary_key=True)
    google_account: Mapped["GoogleAccount"] = relationship("GoogleAccount", back_populates="mails")
    snippet: Mapped[str] = mapped_column(String)
    subject: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)