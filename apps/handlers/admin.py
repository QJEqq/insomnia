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
    admin_pcs_halls_keyboard
)
from database.requests import get_branch, is_admin ,get_computers_all
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
    
