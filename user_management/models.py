from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Integer, ForeignKey, Sequence, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SQLEnum

from user_management.core.database import Base


class Role(Enum):
    SUPERUSER = "SUPERUSER"
    NORMAL_USER = "NORMAL_USER"
    PILOT = "PILOT"


class ClientUser(Base):
    __tablename__ = "client_user"

    client_uid = Column(ForeignKey("client.uid", ondelete="CASCADE"), primary_key=True)
    gcp_user_uid = Column(ForeignKey("gcp_user.uid", ondelete="CASCADE"), primary_key=True)
    role = Column(SQLEnum(Role), nullable=False)

    user = relationship("GCPUser", back_populates="clients")
    client = relationship("Client", back_populates="users")

    def __repr__(self):
        return f"<ClientUser: client_uid={self.client_uid}, user_uid={self.gcp_user_uid}>"


class Client(Base):
    __tablename__ = "client"

    uid = Column(UUID(as_uuid=True), server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    capabilities = relationship("ClientCapability", back_populates="client", cascade="all, delete")
    users = relationship("ClientUser", back_populates="client", cascade="all, delete")
    api_token = relationship(
        "ClientAPIToken", back_populates="client", uselist=False, cascade="all, delete"
    )

    def __repr__(self):
        return f"<Client: uid={self.uid}, name={self.name}>"


class Capability(Base):
    __tablename__ = "capability"

    id = Column(Integer, Sequence("capability_id_seq"), primary_key=True)
    name = Column(String(50), nullable=False, unique=True)

    clients = relationship("ClientCapability", back_populates="capability", cascade="all, delete")

    def __repr__(self):
        return f"<Capability: id={self.id}, name={self.name}>"


class ClientCapability(Base):
    __tablename__ = "client_capability"

    client_uid = Column(ForeignKey("client.uid", ondelete="CASCADE"), primary_key=True)
    capability_id = Column(ForeignKey("capability.id", ondelete="CASCADE"), primary_key=True)

    capability = relationship("Capability", back_populates="clients")
    client = relationship("Client", back_populates="capabilities")

    def __repr__(self):
        return (
            f"<ClientCapability: client_uid={self.client_uid}, capability_id={self.capability_id}>"
        )


class GCPUser(Base):
    __tablename__ = "gcp_user"

    uid = Column(UUID(as_uuid=True), server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    phone_number = Column(String(50))
    staff = Column(Boolean(), default=False, nullable=False)

    clients = relationship("ClientUser", back_populates="user", cascade="all, delete")

    def __repr__(self):
        return f"<GCPUser: uid={self.uid}, email={self.email}>"


class SecurityToken(Base):
    __tablename__ = "security_token"

    uid = Column(UUID(as_uuid=True), server_default=func.uuid_generate_v4(), primary_key=True)
    gcp_user_uid = Column(
        UUID(as_uuid=True), ForeignKey("gcp_user.uid", ondelete="CASCADE"), primary_key=True
    )
    created = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship(
        "GCPUser",
        backref=backref("security_token", uselist=False, cascade="all, delete"),
    )


class ClientAPIToken(Base):
    __tablename__ = "client_api_token"

    client_uid = Column(ForeignKey("client.uid", ondelete="CASCADE"), primary_key=True)
    token = Column(String(128), nullable=False, unique=True)

    client = relationship("Client", back_populates="api_token")

    def __repr__(self):
        return f"<ClientAPIToken: client_uid={self.client_uid}>"
