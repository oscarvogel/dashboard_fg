from django.contrib import admin

from forestal_bot.models import DailySummaryRun, WhatsAppGroup


@admin.register(WhatsAppGroup)
class WhatsAppGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "jid", "account_id", "active", "updated_at")
    search_fields = ("name", "jid")
    list_filter = ("active", "account_id")


@admin.register(DailySummaryRun)
class DailySummaryRunAdmin(admin.ModelAdmin):
    list_display = (
        "operational_date",
        "status",
        "total_groups",
        "total_messages",
        "generated_at",
        "updated_at",
    )
    search_fields = ("idempotency_key", "consolidated_text")
    list_filter = ("status", "operational_date", "source")
    readonly_fields = ("created_at", "updated_at")
