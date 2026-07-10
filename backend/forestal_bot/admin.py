from django.contrib import admin

from forestal_bot.models import WhatsAppGroup


@admin.register(WhatsAppGroup)
class WhatsAppGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "jid", "account_id", "active", "updated_at")
    search_fields = ("name", "jid")
    list_filter = ("active", "account_id")
