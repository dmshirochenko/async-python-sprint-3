from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import expression, func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "awesome_chat"}
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    is_banned = Column(Boolean, server_default=expression.false())  # Database-level default
    ban_until = Column(DateTime)

    messages = relationship("Message", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")
    complaints = relationship("UserComplaint", back_populates="user")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = {"schema": "awesome_chat"}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("awesome_chat.users.id"))
    text = Column(String)
    timestamp = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="messages")


class PrivateMessage(Message):
    __tablename__ = "private_messages"
    __table_args__ = {"schema": "awesome_chat"}

    id = Column(Integer, ForeignKey("awesome_chat.messages.id"), primary_key=True)
    recipient_id = Column(Integer, ForeignKey("awesome_chat.users.id"))

    recipient = relationship("User")


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = {"schema": "awesome_chat"}
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("awesome_chat.users.id"))
    session_token = Column(String)
    is_active = Column(Boolean, server_default=expression.true())

    user = relationship("User", back_populates="sessions")


class UserComplaint(Base):
    __tablename__ = "user_complaints"
    __table_args__ = {"schema": "awesome_chat"}
    id = Column(Integer, primary_key=True)
    complainant_id = Column(Integer, ForeignKey("awesome_chat.users.id"))
    offender_id = Column(Integer, ForeignKey("awesome_chat.users.id"))
    timestamp = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="complaints")


class MessageLimit(Base):
    __tablename__ = "message_limits"
    __table_args__ = {"schema": "awesome_chat"}
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("awesome_chat.users.id"))
    message_count = Column(Integer, server_default=expression.literal(0))
    reset_time = Column(DateTime, server_default=func.now())

    user = relationship("User")
