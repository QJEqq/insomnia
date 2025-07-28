from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import ForeignKey, String, Integer, Boolean, Float, DateTime , Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional

engine = create_async_engine(url='sqlite+aiosqlite:///cyberclub.db',
                             echo=True)

async_session = async_sessionmaker(engine)

class Base(DeclarativeBase):
    pass

class Branch(Base):
    """Филиалы киберклуба (Лесобаза, Московский и т.д.)"""
    __tablename__ = 'branches'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    computers: Mapped[list["Computer"]] = relationship(back_populates="branch")
    halls: Mapped[list["Hall"]] = relationship(back_populates="branch")
    prices: Mapped[list["Price"]] = relationship(back_populates="branch")
    emoji: Mapped[str] = mapped_column(String(10), default='🏢') 

class Hall(Base):
    """Типы залов (standard, vip, bootcamp, tv и т.д.)"""
    __tablename__ = 'halls'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    branch: Mapped["Branch"] = relationship(back_populates="halls")
    computers: Mapped[list["Computer"]] = relationship(back_populates="hall")
    prices: Mapped[list["Price"]] = relationship(back_populates="hall")
    specs: Mapped[str] = mapped_column(Text, nullable=True)

class Computer(Base):
    """Игровые компьютеры"""
    __tablename__ = 'computers'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))  # Номер или название компьютера
    is_busy: Mapped[bool] = mapped_column(Boolean, default=False)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    branch: Mapped["Branch"] = relationship(back_populates="computers")
    hall_id: Mapped[int] = mapped_column(ForeignKey("halls.id"))
    hall: Mapped["Hall"] = relationship(back_populates="computers")

class Price(Base):
    """Цены для разных типов залов и филиалов"""
    __tablename__ = 'prices'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    branch: Mapped["Branch"] = relationship(back_populates="prices")
    hall_id: Mapped[int] = mapped_column(ForeignKey("halls.id"))
    hall: Mapped["Hall"] = relationship(back_populates="prices")
    price_type: Mapped[str] = mapped_column(String(20))  # hourly или package
    period: Mapped[str] = mapped_column(String(20))  # day/night для hourly, название пакета для packages
    amount: Mapped[float] = mapped_column(Float)


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)