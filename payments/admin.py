from django.contrib import admin
from .models import LedgerEntry, Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id','user','wallet','amount','status','created_at']


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ['id','wallet','payment','direction','amount','balance_before','balance_after','created_at']
    list_filter = ['direction','created_at']
    search_fields = ['payment__id','wallet__user__username']
