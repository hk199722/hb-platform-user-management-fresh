from sqlalchemy import Column, ForeignKey, Integer, Table, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from user_management.core.database import Base


client_users = Table(
    "client_users",
    Base.metadata,
    Column("client_uid", ForeignKey("client.uid", ondelete="CASCADE"), primary_key=True),
    Column("gcp_user_uid", ForeignKey("gcp_user.uid", ondelete="CASCADE"), primary_key=True),
)


class Client(Base):
    __tablename__ = "client"

    uid = Column(UUID(as_uuid=True), server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship(
        "GCPUser", secondary=client_users, back_populates="clients", cascade="all, delete"
    )
    farms = relationship("ClientFarm", back_populates="client", cascade="all, delete")


class GCPUser(Base):
    __tablename__ = "gcp_user"

    uid = Column(UUID(as_uuid=True), server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(150), nullable=False)
    phone_number = Column(String(50))
    roles = Column(ARRAY(Integer))

    clients = relationship(
        "Client", secondary=client_users, back_populates="users", passive_deletes=True
    )


class ClientFarm(Base):
    __tablename__ = "client_farm"

    farm_uid = Column(UUID(as_uuid=True), primary_key=True)
    client_uid = Column(UUID(as_uuid=True), ForeignKey("client.uid", ondelete="CASCADE"))

    client = relationship("Client", back_populates="farms")
