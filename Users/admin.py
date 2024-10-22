from django.contrib import admin
from .models import CustomUser, Transaction, Notification

admin.site.register(CustomUser)
admin.site.register(Transaction)
admin.site.register(Notification)