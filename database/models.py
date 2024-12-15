from sqlalchemy import Column, Integer, JSON, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from .db import Base

class Warehouse(Base):
    __tablename__ = "Warehouse"

    id = Column(Integer, primary_key=True)
    x_coord = Column(Float, nullable=False)
    y_coord = Column(Float, nullable=False)

    agents = relationship("AgentsBigPic", back_populates="warehouse")
    orders = relationship("OrdersBigPic", back_populates="warehouse")


class AgentsBigPic(Base):
    __tablename__ = "Agents_bigPic"

    id = Column(Integer, primary_key=True)
    is_checked_in = Column(Boolean, nullable=False, default=False)
    orders = Column(JSON)
    no_of_orders = Column(Integer, nullable=False, default=0)
    total_distance = Column(Integer, nullable=False, default=0)

    warehouse_id = Column(Integer, ForeignKey('Warehouse.id'))
    assigned_orders = relationship("OrdersBigPic", back_populates="assigned_agent")

    warehouse = relationship("Warehouse", back_populates="agents")


class OrdersBigPic(Base):
    __tablename__ = "Orders_bigPic"

    id = Column(Integer, primary_key=True)
    x_coord = Column(Float, nullable=False)
    y_coord = Column(Float, nullable=False)
    is_delivered = Column(Boolean, nullable=False, default=False)

    assigned_agent_id = Column(Integer, ForeignKey('Agents_bigPic.id'))
    warehouse_id = Column(Integer, ForeignKey('Warehouse.id'))

    assigned_agent = relationship("AgentsBigPic", back_populates="assigned_orders")
    warehouse = relationship("Warehouse", back_populates="orders")
