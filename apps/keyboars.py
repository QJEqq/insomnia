from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.requests import get_branches, get_halls, get_prices_by_hall , get_branch
from database.models import AdminRole

start_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="📍 Филиалы", callback_data="branches"),
        InlineKeyboardButton(text="🕒 Свободные места", callback_data="check_places"),
        
    ],
    [
        InlineKeyboardButton(text="💸 Цены", callback_data="prices"),
        InlineKeyboardButton(text="🖥️ Компьютеры", callback_data="pcs"),
    ],
    [
        InlineKeyboardButton(text="ℹ️ Информация", callback_data="info"),
    ]
])

# ---- Меню филиалов ----
async def get_branches_keyboard():
    keyboard = InlineKeyboardBuilder()
    branches = await get_branches()
    
    # Создаем билдер клавиатуры
    
    
    # Добавляем кнопки филиалов (максимум 2 в строке)
    for branch in branches:
        keyboard.add(InlineKeyboardButton(
            text=f"{branch.emoji} {branch.name}",
            callback_data=f"branch:{branch.id}"
        ))
    
    # Добавляем кнопку "Назад" в отдельную строку
    keyboard.row(InlineKeyboardButton(
        text="↩️ Назад",
        callback_data="back_to_start"
    ))
    
    # Настраиваем расположение (2 кнопки в строке для филиалов)
    return keyboard.adjust(2, 1).as_markup()
    
# ---- Карточка филиала ----
def get_branch_details_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        
        [
        InlineKeyboardButton(text="ℹ️ Узнать про свободные компьютеры", callback_data="check_places"),
        ],
        
        [
            InlineKeyboardButton(text="↩️ Назад", callback_data="branches"),
            InlineKeyboardButton(text="🏠 На главную", callback_data="back_to_start"),
        ]
    ])
    
# ---- Раздел "Информация" ----
info_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="📞 Телефон", callback_data="phone"),
        InlineKeyboardButton(text="📢 Telegram", url="https://t.me/insomnia_game_club"),  
    ],
    [
        InlineKeyboardButton(text="🌐 ВКонтакте", url="https://vk.com/insomnia_tyumen"),  
        InlineKeyboardButton(text="✉️ Почта", callback_data="email"),
    ],
    [
        InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_start"),  
    ]
])


# ---- Меню Цены ----

async def price_branches_keyboard():
    keyboard = InlineKeyboardBuilder()
    all_branches = await get_branches()
    for branch in all_branches:
        keyboard.add(InlineKeyboardButton(text=f"{branch.emoji} {branch.name}",
                                          callback_data=f'price_branch:{branch.name}:{branch.id}'))
        
    keyboard.add(InlineKeyboardButton(text="📍 Узнать про филиалы", callback_data="branches"),
                 InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_start") 
                 )
    return keyboard.adjust(1).as_markup()
    

    
# --- Шаг 2: Выбор типа зала ---
async def hall_types_keyboard(branch_id, branch_name):
    keyboard = InlineKeyboardBuilder()
    all_halls = await get_halls(branch_id)
    for hall in all_halls:
        keyboard.row(InlineKeyboardButton(text = f'{hall.name}',
                                          callback_data=f'price_hall:{branch_name}:{hall.name.lower()}:{hall.id}:{branch_id}' ))
    keyboard.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="prices"),
        InlineKeyboardButton(text="🏠 На главную", callback_data="back_to_start")
    )
    return keyboard.as_markup()

async def tariff_keyboard(hall_id: int, branch_name: str, hall_name: str, branch_id):
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(
        InlineKeyboardButton(
            text="⏳ Почасовая", 
            callback_data=f"price_tariff:{branch_name}:{hall_name}:{hall_id}:hourly:{branch_id}"
        ),
        InlineKeyboardButton(
            text="📦 Пакет", 
            callback_data=f"price_tariff:{branch_name}:{hall_name}:{hall_id}:package:{branch_id}"
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            text="↩️ Назад", 
            callback_data=f"price_branch:{branch_name}:{branch_id}"
        ),
        InlineKeyboardButton(text="🏠 На главную", callback_data="back_to_start")
    )
    return keyboard.as_markup()

async def hourly_time_keyboard(hall_id: int, branch_name: str, hall_name: str, branch_id):
    keyboard = InlineKeyboardBuilder()
    prices = await get_prices_by_hall(hall_id)
    
    hourly_prices = [p for p in prices if p.price_type == "hourly"]
    for price in hourly_prices:
        time_name = "День (08:00-17:00)" if "day" in price.period else "Ночь (17:00-08:00)"
        keyboard.add(InlineKeyboardButton(
            text=time_name,
            callback_data=f"price_time:{branch_name}:{hall_name}:{hall_id}:hourly:{price.period}"
        ))
    
    keyboard.row(
        InlineKeyboardButton(
            text="↩️ Назад", 
            callback_data=f"price_hall:{branch_name}:{hall_name.lower()}:{hall_id}:{branch_id}"
        ),
        InlineKeyboardButton(text="🏠 На главную", callback_data="back_to_start")
    )
    
    return keyboard.adjust(1).as_markup()

async def package_keyboard(hall_id: int, branch_name: str, hall_name: str, branch_id):
    keyboard = InlineKeyboardBuilder()
    prices = await get_prices_by_hall(hall_id)
    
    package_prices = [p for p in prices if p.price_type == "package"]
    for price in package_prices:
        if "_" in price.period:
            pkg, time = price.period.split("_")
            btn_text = f"{pkg} ({'дневные' if time == 'day' else 'ночные'})"
        else:
            btn_text = "Ночной пакет (22:00-09:00)" if price.period == "night" else price.period
        
        keyboard.add(InlineKeyboardButton(
            text=btn_text,
            callback_data=f"price_package:{branch_name}:{hall_name}:{hall_id}:{price.period}"
        ))
    
    keyboard.row(
        InlineKeyboardButton(
            text="↩️ Назад", 
            callback_data=f"price_hall:{branch_name}:{hall_name.lower()}:{hall_id}:{branch_id}"
        ),
        InlineKeyboardButton(
            text="🏠 На главную", 
            callback_data="back_to_start"
        )
    )
    return keyboard.adjust(1).as_markup()


async def available_places_keyboard(branch_id: int):
    keyboard = InlineKeyboardBuilder()
    halls = await get_halls(branch_id)
    
    for hall in halls:
        keyboard.add(InlineKeyboardButton(
            text=f"{hall.name}",
            callback_data=f"available_hall:{hall.id}"
        ))
    
    keyboard.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="check_places"),
        InlineKeyboardButton(text="🏠 На главную", callback_data="back_to_start")
    )
    return keyboard.adjust(1).as_markup()

async def back_to_places_keyboard(branch_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="↩️ Назад", callback_data=f"available_branch:{branch_id}"),
            InlineKeyboardButton(text="🏠 На главную", callback_data="back_to_start")
        ]
    ])
    
async def price_branches_keyboard2():
    keyboard = InlineKeyboardBuilder()
    all_branches = await get_branches()
    for branch in all_branches:
        keyboard.add(InlineKeyboardButton(text=f"{branch.emoji} {branch.name}",
                                          callback_data=f'available_branch:{branch.id}'))
        
    keyboard.add(InlineKeyboardButton(text="📍 Узнать про филиалы", callback_data="branches"),
                 InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_start") 
                 )
    return keyboard.adjust(1).as_markup()

# меню компьютеры 

async def pcs_branches_keyboard():
    keyboard = InlineKeyboardBuilder()
    all_branches = await get_branches()
    for branch in all_branches:
        keyboard.add(InlineKeyboardButton(
            text=f"{branch.emoji} {branch.name}",
            callback_data=f"pcs_branch:{branch.id}"
        ))
    keyboard.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_start")
    )
    return keyboard.adjust(1).as_markup()

async def pcs_halls_keyboard(branch_id: int):
    keyboard = InlineKeyboardBuilder()
    all_halls = await get_halls(branch_id)
    for hall in all_halls:
        keyboard.add(InlineKeyboardButton(
            text=f"{hall.name}",
            callback_data=f"pcs_hall:{hall.id}"
        ))
    keyboard.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="pcs"),
        InlineKeyboardButton(text="🏠 На главную", callback_data="back_to_start")
    )
    return keyboard.adjust(1).as_markup()


#admin keyboards


async def admin_main_kb(user_id: int):
    """Асинхронная версия с проверкой прав"""
    from database.requests import check_admin_access  # Локальный импорт
    
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    
    if await check_admin_access(user_id, AdminRole.MANAGER.value):
        builder.button(text="💻 Управление компьютерами", callback_data="admin_computers")
    
    if await check_admin_access(user_id, AdminRole.SUPERADMIN.value):
        builder.button(text="👑 Управление админами", callback_data="admin_manage_admins")
    
    builder.adjust(1)
    return builder.as_markup()

def AdminStartKeyboard(user_id: int):
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="💻 Управление компьютерами", callback_data="admin_computers")
    builder.button(text="👑 Управление админами", callback_data="admin_manage_admins")
    
    builder.adjust(1)
    return builder.as_markup()

def admin_management_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить админа", callback_data="add_admin")
    builder.button(text="📋 Список админов", callback_data="list_admins")
    builder.button(text="⬅️ Назад", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()

async def admin_pcs_branches_keyboard():
    keyboard = InlineKeyboardBuilder()
    all_branches = await get_branches()
    for branch in all_branches:
        keyboard.add(InlineKeyboardButton(
            text=f"{branch.emoji} {branch.name}",
            callback_data=f"admin_pcs_branch:{branch.id}"
        ))
    keyboard.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="back_admin")
    )
    return keyboard.adjust(1).as_markup()

async def admin_pcs_halls_keyboard(branch_id: int):
    keyboard = InlineKeyboardBuilder()
    all_halls = await get_halls(branch_id)
    for hall in all_halls:
        keyboard.add(InlineKeyboardButton(
            text=f"{hall.name}",
            callback_data=f"admin_pcs_hall:{hall.id}:{branch_id}"
        ))
    keyboard.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="admin_computers"),
        InlineKeyboardButton(text="🏠 На главную", callback_data="back_admin")
    )
    return keyboard.adjust(1).as_markup()
async def build_computers_keyboard(branch_id: int, hall_id: int):
    keyboard = InlineKeyboardBuilder()
    
    # Кнопки изменения количества (+1/-1)
    keyboard.row(
        InlineKeyboardButton(
            text="➖1 (Освободить)",
            callback_data=f"comp_dec:{branch_id}:{hall_id}:1"
        ),
        InlineKeyboardButton(
            text="➕1 (Занять)", 
            callback_data=f"comp_inc:{branch_id}:{hall_id}:1"
        )
    )
    
    # Кнопки навигации
    keyboard.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"admin_pcs_branch:{branch_id}"
        ),
        InlineKeyboardButton(
            text="🏠 На главную",
            callback_data="back_admin"
        )
    )
    
    return keyboard.adjust(1).as_markup()


