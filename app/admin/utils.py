import inspect
from sqladmin import ModelView
import app.admin.views as admin_views

def get_admin_views() -> list:
    classes = []
    for name, obj in inspect.getmembers(admin_views):
        if name.endswith('Admin'):
            if inspect.isclass(obj) and obj is not ModelView and issubclass(obj, ModelView):
                classes.append(obj)
    return classes
            