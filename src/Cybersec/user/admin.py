from django.contrib import admin
from .models import SOCUser, NonSOCUser, CustomUser

admin.site.register(SOCUser)
admin.site.register(NonSOCUser)
admin.site.register(CustomUser)