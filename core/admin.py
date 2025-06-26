from django.contrib import admin
from .models import Sender, Transaction, Receiver

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'currency')
    search_fields = ('sender__username', 'receiver__username')

@admin.register(Sender)
class SenderAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'id_number')
    search_fields = ('full_name', 'phone', 'id_number')

@admin.register(Receiver)
class ReceiverAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'phone', 'bank_name', 'sender', 'account_number')
    search_fields = ('name', 'country', 'phone')
