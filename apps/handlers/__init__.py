from .user import router as user_router
from .admin import router as admin_router
routers = [user_router, admin_router]

all = ['routers', 'user_router', 'admin_router' ]