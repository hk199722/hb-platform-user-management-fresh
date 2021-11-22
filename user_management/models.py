from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from user_management.core.database import Base


class ClientUser(Base):
    __tablename__ = "client_user"
    client_uid = Column(ForeignKey("client.uid", ondelete="CASCADE"), primary_key=True)
    gcp_user_uid = Column(ForeignKey("gcp_user.uid", ondelete="CASCADE"), primary_key=True)
    role = Column(String(15))

    user = relationship("GCPUser", back_populates="clients", cascade="all, delete")
    client = relationship("Client", back_populates="users")


class Client(Base):
    __tablename__ = "client"

    uid = Column(UUID(as_uuid=True), server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship("ClientUser", back_populates="client", cascade="all, delete")
    farms = relationship("ClientFarm", back_populates="client", cascade="all, delete")


class GCPUser(Base):
    __tablename__ = "gcp_user"

    uid = Column(UUID(as_uuid=True), server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    phone_number = Column(String(50))
    roles = Column(ARRAY(Integer))

    clients = relationship("ClientUser", back_populates="user", cascade="all, delete")


class ClientFarm(Base):
    __tablename__ = "client_farm"

    farm_uid = Column(UUID(as_uuid=True), primary_key=True)
    client_uid = Column(UUID(as_uuid=True), ForeignKey("client.uid", ondelete="CASCADE"))

    client = relationship("Client", back_populates="farms")
