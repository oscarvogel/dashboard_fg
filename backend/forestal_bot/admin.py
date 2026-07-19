from django.contrib import admin

from forestal_bot.models import (
    DailySummaryRun,
    WeighingMeasurement,
    WeighingMeasurementRevision,
    WeighingMovement,
    WhatsAppGroup,
)


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


class WeighingMeasurementInline(admin.TabularInline):
    model = WeighingMeasurement
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(WeighingMovement)
class WeighingMovementAdmin(admin.ModelAdmin):
    list_display = (
        "operational_date",
        "plate_normalized",
        "driver_name",
        "status",
        "official_scale",
        "updated_at",
    )
    list_filter = (
        "organization_key",
        "origin_group_key",
        "status",
        "official_scale",
        "operational_date",
    )
    search_fields = (
        "idempotency_key",
        "plate_normalized",
        "plate_original",
        "driver_name",
        "source_message_ids",
    )
    readonly_fields = ("id", "plate_normalized", "created_at", "updated_at")
    inlines = (WeighingMeasurementInline,)


@admin.register(WeighingMeasurement)
class WeighingMeasurementAdmin(admin.ModelAdmin):
    list_display = (
        "movement",
        "scale",
        "kind",
        "weight_kg",
        "source",
        "measured_at",
    )
    list_filter = ("scale", "kind", "source")
    search_fields = (
        "idempotency_key",
        "movement__plate_normalized",
        "evidence_id",
        "message_id",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(WeighingMeasurementRevision)
class WeighingMeasurementRevisionAdmin(admin.ModelAdmin):
    list_display = (
        "measurement",
        "revision",
        "weight_kg",
        "source",
        "recorded_at",
    )
    list_filter = ("source", "recorded_at")
    search_fields = (
        "idempotency_key",
        "measurement__movement__plate_normalized",
        "evidence_id",
        "message_id",
    )
    readonly_fields = (
        "measurement",
        "revision",
        "idempotency_key",
        "weight_kg",
        "source",
        "evidence_id",
        "message_id",
        "measured_at",
        "correction_reason",
        "recorded_at",
    )
