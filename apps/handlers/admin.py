import asyncio
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message , CallbackQuery
from database.models import async_session
from apps.keyboars import (
    AdminStartKeyboard,
    admin_pcs_branches_keyboard,
    admin_pcs_halls_keyboard,
    build_computers_keyboard
)
from database.requests import get_branch, is_admin ,get_computers_all, get_computers_stats, get_hall, set_computers_status
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class ComputerState(StatesGroup):
    waiting_amount = State()
router = Router()


@router.message(Command('admin'))
async def admin_panel(message : Message):
    await asyncio.sleep(0.2)
    user_id = message.from_user.id
    admin_role = await is_admin(user_id)
    if admin_role is not None:
        await message.answer (
            '📚 <b> Админ панель </b> 📚',
            reply_markup=AdminStartKeyboard(user_id),
            parse_mode="HTML"
        )
    else:
        await message.answer("Доступ запрещен!")
@router.callback_query(F.data == 'back_admin')
async def main_panel(callback : CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text (
            '📚 <b> Админ панель </b> 📚',
            reply_markup=AdminStartKeyboard(user_id),
            parse_mode="HTML"
        )
        
@router.callback_query(F.data == "admin_stats")
async def admin_stat(callback : CallbackQuery):
    await asyncio.sleep(0.2)
    admin_role = await is_admin(callback.from_user.id)
    if admin_role is not None:
        stats = await get_computers_all()  
    
        text = (
            "📊 <b>Статистика по компьютерам</b>\n\n"
            f"▪ Всего компьютеров: <b>{stats['total']}</b>\n"
            f"🟢 Свободных: <b>{stats['free']}</b>\n"
            f"🔴 Занятых: <b>{stats['busy']}</b>"
        )

        # Создаём клавиатуру с кнопкой "Назад"
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="back_admin"  
            )
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text('Ошибка')

@router.callback_query(F.data == 'admin_computers')
async def admin_branch(callback : CallbackQuery):
    await callback.message.edit_text(
        " Выберите филиал ",
        reply_markup=await admin_pcs_branches_keyboard()
    )
    
@router.callback_query(F.data.startswith("admin_pcs_branch:"))
async def show_pcs_halls(callback: CallbackQuery):
    branch_id = int(callback.data.split(":")[1])
    branch = await get_branch(branch_id)
    await callback.message.edit_text(
        f"🏢 Филиал: {branch.name}\nВыберите зал:",
        reply_markup=await admin_pcs_halls_keyboard(branch_id)
    )

        
@router.callback_query(F.data.startswith('admin_pcs_hall:'))
async def computer_panel(callback : CallbackQuery):
    fall = None
    parts = callback.data.split(':')
    branch_id = int(parts[2])
    hall_id = int(parts[1])
    
    branch = await get_branch(branch_id)
    hall = await get_hall(hall_id)
    await asyncio.sleep(0.2)
    admin_role = await is_admin(callback.from_user.id)
    if admin_role is not None:
        stats = await get_computers_stats(branch_id,hall_id)  
        keyboard = await build_computers_keyboard(branch_id, hall_id)
        
        text = (
            f" <b>🏢 Филиал: {branch.name}\nЗал: {hall.name}</b>\n\n"
            f"▪ Всего компьютеров: <b>{stats['total']}</b>\n"
            f"🟢 Свободных: <b>{stats['free']}</b>\n"
            f"🔴 Занятых: <b>{stats['busy']}</b>"
        )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()



@router.callback_query(F.data.startswith("comp_dec:"))  # Обработчик для -1
async def decrease_computers_handler(callback: CallbackQuery):
    """Уменьшает количество занятых компьютеров на 1"""
    try:
        # Разбираем callback_data: "comp_dec:{branch_id}:{hall_id}:1"
        _, branch_id, hall_id, _ = callback.data.split(':')
        branch_id = int(branch_id)
        hall_id = int(hall_id)
        
        # Получаем текущую статистику
        stats = await get_computers_stats(branch_id, hall_id)
        
        # Вычисляем новое количество (не меньше 0)
        new_busy = max(0, stats['busy'] - 1)
        
        # Обновляем статусы в БД
        success = await set_computers_status(branch_id, hall_id, new_busy)
        
        if success:
            await callback.answer("✅ Освободил 1 компьютер")
            await update_computer_panel(callback, branch_id, hall_id)
        else:
            await callback.answer("❌ Ошибка при обновлении", show_alert=True)
            
    except Exception as e:
        await callback.answer(f"⚠️ Ошибка: {str(e)}", show_alert=True)

@router.callback_query(F.data.startswith("comp_inc:"))  # Обработчик для +1
async def increase_computers_handler(callback: CallbackQuery):
    """Увеличивает количество занятых компьютеров на 1"""
    try:
        # Разбираем callback_data: "comp_inc:{branch_id}:{hall_id}:1"
        _, branch_id, hall_id, _ = callback.data.split(':')
        branch_id = int(branch_id)
        hall_id = int(hall_id)
        
        # Получаем текущую статистику
        stats = await get_computers_stats(branch_id, hall_id)
        
        # Проверяем, есть ли свободные компьютеры
        if stats['free'] <= 0:
            await callback.answer("❌ Нет свободных компьютеров", show_alert=True)
            return
        
        # Увеличиваем количество занятых
        new_busy = stats['busy'] + 1
        
        # Обновляем статусы в БД
        success = await set_computers_status(branch_id, hall_id, new_busy)
        
        if success:
            await callback.answer("✅ Занял 1 компьютер")
            await update_computer_panel(callback, branch_id, hall_id)
        else:
            await callback.answer("❌ Ошибка при обновлении", show_alert=True)
            
    except Exception as e:
        await callback.answer(f"⚠️ Ошибка: {str(e)}", show_alert=True)

async def update_computer_panel(callback: CallbackQuery, branch_id: int, hall_id: int):
    """Обновляет сообщение с панелью компьютеров"""
    try:
        # Получаем актуальные данные
        branch = await get_branch(branch_id)
        hall = await get_hall(hall_id)
        stats = await get_computers_stats(branch_id, hall_id)
        
        # Формируем текст
        text = (
            f"<b>🏢 Филиал: {branch.name}\n"
            f"🖥 Зал: {hall.name}</b>\n\n"
            f"▪ Всего: <b>{stats['total']}</b>\n"
            f"🟢 Свободно: <b>{stats['free']}</b>\n"
            f"🔴 Занято: <b>{stats['busy']}</b>"
        )
        
        # Обновляем клавиатуру
        keyboard = await build_computers_keyboard(branch_id, hall_id)
        
        # Редактируем сообщение
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
    except Exception as e:
        await callback.answer(f"⚠️ Ошибка обновления: {str(e)}", show_alert=True)
