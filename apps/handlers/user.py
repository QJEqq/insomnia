from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
import asyncio
from apps.keyboars import info_keyboard, start_keyboard,  get_branch_details_keyboard , \
                                get_branches_keyboard, price_branches_keyboard, hall_types_keyboard , tariff_keyboard, \
                                hourly_time_keyboard, package_keyboard, available_places_keyboard, back_to_places_keyboard,\
                                price_branches_keyboard2, pcs_branches_keyboard , pcs_halls_keyboard
from database.requests import get_price, get_hall, get_branch, get_available_computers, get_available_computers_count, get_branches
from datetime import datetime

router = Router()



@router.message(CommandStart())
async def cmd_start(message: Message):
    await asyncio.sleep(0.3)
    await message.answer(
    "✨ <b>Добро пожаловать в Insomnia</b> ✨\n\n"
    "Я помогу тебе:\n"
    "• Узнать адреса филиалов 🏢\n"
    "• Проверить свободные места в реальном времени 🕒\n"
    "• Узнать цены 💸\n"
    "• Узнать характеристики 💻",
    reply_markup=start_keyboard,
    parse_mode="HTML"
)
    


@router.callback_query(F.data == "branches")
async def show_branches(callback: CallbackQuery):
    await asyncio.sleep(0.1)
    await callback.message.edit_text(
        "📍 Выбери район:",
        reply_markup=await get_branches_keyboard(),
        parse_mode="Markdown"
    )
    


@router.callback_query(F.data.startswith("branch:"))
async def show_branch_details(callback: CallbackQuery):
    
    await asyncio.sleep(0.1)
    
    branch = callback.data.split(":")[1]
    
    if branch == "1":
        text = (
            "🗺 [Карта 2ГИС](https://2gis.ru/tyumen/firm/70000001083620594/65.662717%2C57.159974?m=65.66474%2C57.160166%2F17.37)\n\n"
            "🌳 Филиал Лесобаза\n"
            "• Адрес: Улица Судостроителей, 40/2\n"
            "• Часы работы: Круглосуточно\n"
            "• Телефон: +7 (982) 971‒72‒28\n"
            "• Доступные залы: Standart, Vip, Bootcamp"
        )
    elif branch == "2":
        text = (
            "🗺 [Карта 2ГИС](https://2gis.ru/tyumen/branches/70000001083620593/firm/70000001098698503?m=65.500298%2C57.130425%2F16.69)\n\n"
            "🏙️ Филиал Московский\n"
            "• Адрес: Московский тракт, 87 к1 этаж\n"
            "• Часы работы: Круглосуточно\n"
            "• Телефон: +7 (982) 961‒40‒04\n"
            "• Доступные залы: Standart, Vip, Tv"
        )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_branch_details_keyboard(),
        parse_mode="Markdown",
        disable_web_page_preview=False
    )

# ---- Назад в главное меню ----
@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    await asyncio.sleep(0.1)
    await callback.message.edit_text(
        "✨ <b>Главное меню</b> ✨",
        reply_markup=start_keyboard,
        parse_mode="HTML"
    )
    


@router.callback_query(F.data == "info")
async def show_info(callback: CallbackQuery):
    await asyncio.sleep(0.1)
    await callback.message.edit_text(
        "📌 <b>Контактная информация:</b>\n\n"
        "• Телефон: +7 (982) 961‒40‒04\n"
        "• Telegram: @insomnia_game_club\n"
        "• ВКонтакте: https://vk.com/insomnia_tyumen\n"
        "• Почта: insomnia.gameclub72@gmail.com",
        reply_markup=info_keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "phone")
async def send_phone(callback: CallbackQuery):
    await callback.answer("☎️ Позвоните нам: +7 (982) 961‒40‒04", show_alert=True)

@router.callback_query(F.data == "email")
async def send_email(callback: CallbackQuery):
    await callback.answer("📩 Напишите нам: insomnia.gameclub72@gmail.com", show_alert=True)
    
# --- Данные прайс-листа ---



@router.callback_query(F.data == "prices")
async def show_price_branches(callback: CallbackQuery):
    await callback.message.edit_text(
        "💸 Выберите филиал:",
        reply_markup=await price_branches_keyboard()
    )



@router.callback_query(F.data.startswith("price_branch:"))
async def show_hall_types(callback: CallbackQuery):
    branch_name = callback.data.split(":")[1]
    branch_id = callback.data.split(":")[2]
    await callback.message.edit_text(
        f"🏢 Филиал: {branch_name.capitalize()}\nВыберите тип зала:",
        reply_markup=await hall_types_keyboard(branch_id, branch_name)
    )



@router.callback_query(F.data.startswith("price_hall:"))
async def show_tariffs(callback: CallbackQuery):
    _, branch_name, hall_name, hall_id, branch_id = callback.data.split(":")
    await callback.message.edit_text(
        f"🏢 {branch_name.capitalize()} | 🚪 {hall_name.capitalize()}\nВыберите тариф:",
        reply_markup=await tariff_keyboard(hall_id,branch_name, hall_name,branch_id)
    )



@router.callback_query(F.data.startswith("price_hall:"))
async def show_tariffs(callback: CallbackQuery):
    _, branch_name, hall_name, hall_id = callback.data.split(":")
    await callback.message.edit_text(
        f"🏢 {branch_name.capitalize()} | 🚪 {hall_name.capitalize()}\nВыберите тариф:",
        reply_markup=await tariff_keyboard(int(hall_id), branch_name, hall_name)
    )

@router.callback_query(F.data.startswith("price_tariff:"))
async def show_time_options(callback: CallbackQuery):
    _, branch_name, hall_name, hall_id, tariff, branch_id = callback.data.split(":")
    if tariff == "hourly":
        await callback.message.edit_text(
            "⏳ Выберите время:",
            reply_markup=await hourly_time_keyboard(int(hall_id), branch_name, hall_name, branch_id)
        )
    else:
        await callback.message.edit_text(
            "📦 Доступные пакеты:",
            reply_markup=await package_keyboard(int(hall_id), branch_name, hall_name, branch_id)
        )

@router.callback_query(F.data.startswith("price_time:"))
async def show_hourly_price(callback: CallbackQuery):
    _, branch_name, hall_name, hall_id, _, period = callback.data.split(":")
    price = await get_price(int(hall_id), "hourly", period)
    
    time_range = "08:00-17:00" if period == "day" else "17:00-08:00"
    await callback.message.edit_text(
        f"🏢 Филиал: {branch_name.capitalize()}\n"
        f"🚪 Зал: {hall_name.capitalize()}\n"
        f"⏳ Время: {time_range}\n"
        f"💸 Цена: {price.amount} руб/час\n\n"
        f"Итоговая стоимость рассчитывается при бронировании",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🏠 На главную", callback_data="back_to_start")
        ]])
    )

@router.callback_query(F.data.startswith("price_package:"))
async def show_package_price(callback: CallbackQuery):
    _, branch_name, hall_name, hall_id, period = callback.data.split(":")
    price = await get_price(int(hall_id), "package", period)
    
    if "_" in period:
        pkg, time = period.split("_")
        text = f"📦 Пакет {pkg}\n⏱ Время: {'08:00-17:00' if time == 'day' else '17:00-08:00'}"
    else:
        text = "🌙 Ночной пакет (22:00-09:00)"
    
    await callback.message.edit_text(
        f"🏢 Филиал: {branch_name.capitalize()}\n"
        f"🚪 Зал: {hall_name.capitalize()}\n"
        f"{text}\n💸 Цена: {price.amount} руб",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🏠 На главную", callback_data="back_to_start")
        ]])
    )

# Свободные места

@router.callback_query(F.data == "check_places")
async def check_places(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏢 Выберите филиал:",
        reply_markup=await price_branches_keyboard2()  
    )

@router.callback_query(F.data.startswith("available_branch:"))
async def show_available_halls(callback: CallbackQuery):
    branch_id = int(callback.data.split(":")[1])
    branch = await get_branch(branch_id)
    
    await callback.message.edit_text(
        f"🏢 Филиал: {branch.name}\nВыберите зал:",
        reply_markup=await available_places_keyboard(branch_id)
    )

@router.callback_query(F.data.startswith("available_hall:"))
async def show_available_computers(callback: CallbackQuery):
    hall_id = int(callback.data.split(":")[1])
    hall = await get_hall(hall_id)
    branch = await get_branch(hall.branch_id)
    
    # Получаем свободные компьютеры
    available = await get_available_computers(hall.branch_id, hall.id)
    current_time = datetime.now().strftime("%H:%M")
    
    await callback.message.edit_text(
        f"🏢 Филиал: {branch.name}\n"
        f"🚪 Зал: {hall.name}\n"
        f"⏰ Текущее время: {current_time}\n"
        f"🆓 Свободных компьютеров: {len(available)}",
        reply_markup=await back_to_places_keyboard(hall.branch_id)
    )

#меню компьютеры
    
@router.callback_query(F.data == "pcs")
async def show_pcs_branches(callback: CallbackQuery):
    await callback.message.edit_text(
        "🖥️ Выберите филиал:",
        reply_markup=await pcs_branches_keyboard()
    )

@router.callback_query(F.data.startswith("pcs_branch:"))
async def show_pcs_halls(callback: CallbackQuery):
    branch_id = int(callback.data.split(":")[1])
    branch = await get_branch(branch_id)
    await callback.message.edit_text(
        f"🏢 Филиал: {branch.name}\nВыберите зал:",
        reply_markup=await pcs_halls_keyboard(branch_id)
    )

@router.callback_query(F.data.startswith("pcs_hall:"))
async def show_hall_specs(callback: CallbackQuery):
    hall_id = int(callback.data.split(":")[1])
    hall = await get_hall(hall_id)
    branch = await get_branch(hall.branch_id)
    
    await callback.message.edit_text(
        f"*🏢 Филиал:* {branch.name}\n"
        f"*🚪 Зал:* {hall.name}\n\n"
        f"*💻 Характеристики:*\n"
        f"`{hall.specs.replace('\\n', '\n')}`",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 На главную", callback_data="back_to_start")]
        ])
    )
