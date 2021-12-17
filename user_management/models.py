from enum import Enum

from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
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

    users = relationship("ClientUser", back_populates="client", cascade="all, delete")
    farms = relationship("ClientFarm", back_populates="client", cascade="all, delete")

    def __repr__(self):
        return f"<Client: uid={self.uid}, name={self.name}>"


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


class ClientFarm(Base):
    __tablename__ = "client_farm"

    farm_uid = Column(UUID(as_uuid=True), primary_key=True)
    client_uid = Column(UUID(as_uuid=True), ForeignKey("client.uid", ondelete="CASCADE"))

    client = relationship("Client", back_populates="farms")

    def __repr__(self):
        return f"<ClientFarm: farm_uid={self.farm_uid}, client_uid={self.client_uid}>"
