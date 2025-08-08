import asyncio
from datetime import datetime
from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message , CallbackQuery
from database.models import Admin, async_session , AdminRole
from apps.keyboars import (
    AdminStartKeyboard,
    admin_pcs_branches_keyboard,
    admin_pcs_halls_keyboard,
    build_computers_keyboard,
    admin_management_kb,
    roles_kb
)
from database.requests import get_branch, is_admin ,get_computers_all, get_computers_stats, get_hall, set_computers_status , show_admins, get_admin_by_id, delete_admin, update_admin_role, get_user_role
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class ComputerState(StatesGroup):
    waiting_amount = State()
    
class AdminActions(StatesGroup):
    waiting_admin_id = State()
    waiting_new_role = State()
    waiting_delete_id = State()
    
class AddAdminStates(StatesGroup):
    waiting_tg_id = State()
    waiting_name = State()
    waiting_role = State()  

router = Router()


@router.message(Command('admin'))
async def admin_panel(message : Message):
    await asyncio.sleep(0.2)
    user_id = message.from_user.id
    user_role = await get_user_role(user_id)
    admin_role = await is_admin(user_id)
    if admin_role is not None:
        await message.answer (
            '📚 <b> Админ панель </b> 📚',
            reply_markup=AdminStartKeyboard(user_role),
            parse_mode="HTML"
        )
    else:
        await message.answer("Доступ запрещен!")
@router.callback_query(F.data == 'back_admin')
async def main_panel(callback : CallbackQuery):
    user_role = await get_user_role(callback.from_user.id)
    admin_role = await is_admin(callback.from_user.id)
    if admin_role is not None:
        await callback.message.edit_text (
                '📚 <b> Админ панель </b> 📚',
                reply_markup=AdminStartKeyboard(user_role),
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

# START - управление компьютерами

@router.callback_query(F.data == 'admin_computers')
async def admin_branch(callback : CallbackQuery):
    admin_role = await is_admin(callback.from_user.id)
    if admin_role is not None:
        await callback.message.edit_text(
            " Выберите филиал ",
            reply_markup=await admin_pcs_branches_keyboard()
        )
    
@router.callback_query(F.data.startswith("admin_pcs_branch:"))
async def show_pcs_halls(callback: CallbackQuery):
    admin_role = await is_admin(callback.from_user.id)
    if admin_role is not None:
        branch_id = int(callback.data.split(":")[1])
        branch = await get_branch(branch_id)
        await callback.message.edit_text(
            f"🏢 Филиал: {branch.name}\nВыберите зал:",
            reply_markup=await admin_pcs_halls_keyboard(branch_id)
        )


@router.callback_query(F.data.startswith('admin_pcs_hall:'))
async def computer_panel(callback : CallbackQuery):
    admin_role = await is_admin(callback.from_user.id)
    if admin_role is not None:
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
    admin_role = await is_admin(callback.from_user.id)
    if admin_role is not None:
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
    admin_role = await is_admin(callback.from_user.id)
    if admin_role is not None:
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
    admin_role = await is_admin(callback.from_user.id)
    if admin_role is not None:
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
        
# END - управление компьютерами

# START - управление админами 

@router.callback_query(F.data == 'admin_manage_admins')
async def superadmin_panel(callback: CallbackQuery):
    await asyncio.sleep(0.2)
    user_id = callback.from_user.id
    admin_role = await is_admin(user_id)
    if admin_role is not None:
        await callback.message.edit_text (
            '👑 <b> Управление админами </b> 👑',
            parse_mode="HTML",
            reply_markup=admin_management_kb()
            
        )
    else:
        await callback.message.edit_text("Доступ запрещен!")
        
async def get_username_by_id(bot: Bot, user_id: int):
    try:
        chat = await bot.get_chat(user_id)
        return chat.username  # Вернет None, если username нет
    except Exception as e:
        print(f"Ошибка: {e}")
        return None
    
@router.callback_query(F.data == 'list_admins')
async def list_admins( callback : CallbackQuery):
    admin_role = await is_admin(callback.from_user.id)
    if admin_role is not None:
        await asyncio.sleep(0.2)
        bot = callback.bot
        admins = await show_admins()
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="↩️ Назад",
            callback_data="admin_manage_admins"
        ))
        text = "Список админов:\n"
        for idx, admin in enumerate(admins, 1):
            username = await get_username_by_id(bot, admin.user_id)
            username_display = f"@{username}" if username else "—"
            role_name = AdminRole(admin.role).display_name
            text += f"{admin.id} | {admin.full_name} | {username_display} | {role_name} | {admin.created_at}\n"

        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup()
        )
        await callback.answer()
    
@router.callback_query(F.data == "edit_admin")
async def start_edit_admin(callback: CallbackQuery, state: FSMContext):
    admin_role = await is_admin(callback.from_user.id)
    if admin_role is not None:
        await state.set_state(AdminActions.waiting_admin_id)
        keyboard = InlineKeyboardBuilder()
        keyboard.row(  # Добавляем кнопки в один ряд
            InlineKeyboardButton(
                text="📋 Список админов",
                callback_data="list_admins"
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="cancel_action"
            )
        )
        await callback.message.edit_text(
            "Введите ID админа для изменения (цифра):\n\n",
            reply_markup=keyboard.as_markup()
        )
    
@router.message(AdminActions.waiting_admin_id)
async def process_admin_id(message: Message, state: FSMContext):
    try:
        admin_id = int(message.text)
        admin = await get_admin_by_id(admin_id)
        
        if not admin:
            await message.answer("Админ не найден! Попробуйте еще раз:")
            return
            
        await state.update_data(admin_id=admin_id)
        await state.set_state(AdminActions.waiting_new_role)
        
        await message.answer(
            f"Выбран админ: {admin.full_name}\n"
            "Выберите новую роль:",
            reply_markup=await roles_kb()
        )
    except ValueError:
        await message.answer("Пожалуйста, введите число (ID админа):")
        

# Обработка выбора роли
@router.callback_query(AdminActions.waiting_new_role, F.data.startswith("role_"))
async def process_role_selection(callback: CallbackQuery, state: FSMContext):
    admin_role = await is_admin(callback.from_user.id)
    if admin_role is not None:
        role_map = {
            "role_1": 1,
            "role_2": 2,
            "role_3": 3
        }
        
        data = await state.get_data()
        await update_admin_role(data['admin_id'], role_map[callback.data])
        
        await callback.message.edit_text("✅ Роль админа успешно изменена!")
        await state.clear()
        await superadmin_panel(callback)

# Начало удаления админа
@router.callback_query(F.data == "delete_admin")
async def start_delete_admin(callback: CallbackQuery, state: FSMContext):
    admin_role = await is_admin(callback.from_user.id)
    if admin_role is not None:
        await state.set_state(AdminActions.waiting_delete_id)
        keyboard = InlineKeyboardBuilder()
        keyboard.row(  # Добавляем кнопки в один ряд
            InlineKeyboardButton(
                text="📋 Список админов",
                callback_data="list_admins"
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="cancel_action"
            )
        )
        await callback.message.edit_text(
            "Введите ID админа для удаления:\n\n",
            reply_markup=keyboard.as_markup()
        )

# Обработка удаления админа
@router.message(AdminActions.waiting_delete_id)
async def process_delete_admin(message: Message, state: FSMContext):
    try:
        admin_id = int(message.text)
        success = await delete_admin(admin_id)
        
        if success:
            await message.answer("✅ Админ успешно удален!")
        else:
            await message.answer("❌ Админ не найден!")
            
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число (ID админа):")
        

@router.callback_query(F.data == 'add_admin')
async def start_add_admin(callback : CallbackQuery , state : FSMContext):
    await state.set_state(AddAdminStates.waiting_tg_id)
    await callback.message.edit_text(
        "Введите Telegram ID нового админа (только цифры):",
        reply_markup=InlineKeyboardBuilder()
            .button(text="❌ Отмена", callback_data="cancel_action")
            .as_markup()
    )
    await callback.answer()

@router.message(AddAdminStates.waiting_tg_id)
async def process_tg_id(message: Message, state: FSMContext):
    try:
        tg_id = int(message.text)
        await state.update_data(tg_id=tg_id)
        await state.set_state(AddAdminStates.waiting_name)
        await message.answer(
            "Теперь введите имя нового админа:",
            reply_markup=InlineKeyboardBuilder()
                .button(text="❌ Отмена", callback_data="cancel_add_admin")
                .as_markup()
        )
    except ValueError:
        await message.answer("Некорректный ID! Введите только цифры:")

# Обработка имени
@router.message(AddAdminStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    if len(message.text) < 2:
        await message.answer("Имя слишком короткое! Введите еще раз:")
        return
        
    await state.update_data(full_name=message.text)
    await state.set_state(AddAdminStates.waiting_role)
    await message.answer(
        "Выберите роль для админа:",
        reply_markup=await roles_kb()
    )

# Обработка выбора роли
@router.callback_query(AddAdminStates.waiting_role, F.data.startswith("role_"))
async def process_role(callback: CallbackQuery, state: FSMContext):
    admin_role = await is_admin(callback.from_user.id)
    if admin_role is not None:
        role_mapping = {
            "role_1": 1,
            "role_2": 2,
            "role_3": 3
        }
        
        data = await state.get_data()
        role_value = role_mapping[callback.data]
        
        # Добавляем админа в БД
        async with async_session() as session:
            try:
                session.add(Admin(
                    user_id=data['tg_id'],
                    full_name=data['full_name'],
                    role=role_value,
                    is_active=True,
                    created_at=datetime.now()
                ))
                await session.commit()
                
                role_name = AdminRole(role_value).display_name
                await callback.message.edit_text(
                    f"✅ Админ успешно добавлен!\n\n"
                    f"ID: {data['tg_id']}\n"
                    f"Имя: {data['full_name']}\n"
                    f"Роль: {role_name}",
                    reply_markup=InlineKeyboardBuilder()
                        .button(text="⬅️ Назад", callback_data="admin_manage_admins")
                        .as_markup()
                )
            except Exception as e:
                await callback.message.answer(
                    f"❌ Ошибка при добавлении: {str(e)}",
                    reply_markup=InlineKeyboardBuilder()
                        .button(text="Попробовать снова", callback_data="add_admin")
                        .as_markup()
                )
            finally:
                await state.clear()
        


@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await superadmin_panel(callback)