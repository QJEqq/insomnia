from database.models import AdminRole, Branch, Hall, Computer, async_session, Price , Admin , AdminLog
from sqlalchemy import func, select, update 
from typing import Optional 
from sqlalchemy import select, update, insert
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# users methods
async def get_branches():
    async with async_session() as session:
        result = await session.execute(select(Branch))
        return result.scalars().all()  
    
async def get_halls(branch_id):
    async with async_session() as session:
        return await session.scalars(select(Hall).where(Hall.branch_id == branch_id))

async def get_prices_by_hall(hall_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Price).where(Price.hall_id == hall_id))
        return result.scalars().all()

async def get_price(hall_id: int, price_type: str, period: str):
    async with async_session() as session:
        result = await session.execute(
            select(Price).where(
                Price.hall_id == hall_id,
                Price.price_type == price_type,
                Price.period == period
            ))
        return result.scalar_one_or_none()
    
async def get_available_computers(branch_id: int, hall_id: int = None):
    async with async_session() as session:
        query = select(Computer).where(
            Computer.branch_id == branch_id,
            Computer.is_busy == False
        )
        if hall_id:
            query = query.where(Computer.hall_id == hall_id)
        
        result = await session.execute(query)
        return result.scalars().all()
    
async def get_branch(branch_id: int):
    async with async_session() as session:
        result = await session.execute(select(Branch).where(Branch.id == branch_id))
        return result.scalar_one()

async def get_hall(hall_id: int) -> Optional[Hall]:
    """Безопасное получение зала с обработкой отсутствия"""
    async with async_session() as session:
        result = await session.execute(
            select(Hall)
            .where(Hall.id == hall_id)
        )
        return result.scalar_one_or_none()  # Возвращает None если зал не найден
    
async def get_available_computers_count(branch_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(func.count(Computer.id))
            .where(
                Computer.branch_id == branch_id,
                Computer.is_busy == False
            )
        )
        return result.scalar()

#admins methods

async def is_admin(user_id):
    async with async_session() as session:
        try:
            result = await session.execute(
                select(Admin)
                .where(
                    Admin.user_id == user_id,
                    Admin.is_active == True
                )
            )
            admin = result.scalar_one_or_none()
            
            if admin is not None:
                return AdminRole(admin.role)
            return None
            
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при проверке админа {user_id}: {e}")
            return None

async def get_computers_all():
    async with async_session() as session:
        # Общее количество компьютеров по всем филиалам
        total_result = await session.execute(select(func.count(Computer.id)))
        total = total_result.scalar()
        
        # Количество свободных компьютеров
        free_result = await session.execute(
            select(func.count(Computer.id))
            .where(Computer.is_busy == False)
        )
        free = free_result.scalar()
        
        # Количество занятых компьютеров
        busy = total - free
        
        return {
            'total': total,
            'free': free,
            'busy': busy
        }   
    
