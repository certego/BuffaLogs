from django.contrib import admin
from .models import User, Login, Alert, UsersIP, TaskSettings, Config

admin.site.register(User)
admin.site.register(Login)
admin.site.register(Alert)
admin.site.register(UsersIP)
admin.site.register(TaskSettings)
admin.site.register(Config)
