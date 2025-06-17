from django.contrib import admin
from .models import Sender

@admin.register(Sender)
class SenderAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'id_number')
    search_fields = ('full_name', 'phone_number', 'id_number')
