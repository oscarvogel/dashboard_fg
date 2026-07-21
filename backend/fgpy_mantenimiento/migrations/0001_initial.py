# Generated for the isolated FGPY maintenance app.
import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FgpyMaintenanceIncident",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("organization_key", models.CharField(db_index=True, default="forestal-paraguay", max_length=64)),
                ("fgpy_equipment_external_id", models.CharField(blank=True, db_index=True, max_length=64, null=True)),
                ("fgpy_equipment_display", models.CharField(blank=True, default="", max_length=255)),
                ("fgpy_equipment_code", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Abierta"),
                            ("resolved", "Resuelta"),
                            ("cancelled", "Cancelada"),
                            ("requires_review", "Requiere revision"),
                        ],
                        db_index=True,
                        default="open",
                        max_length=24,
                    ),
                ),
                (
                    "operational_status",
                    models.CharField(
                        choices=[
                            ("stopped", "Parada"),
                            ("operating", "Operando"),
                            ("intermittent", "Intermitente"),
                            ("unknown", "Desconocido"),
                        ],
                        default="unknown",
                        max_length=24,
                    ),
                ),
                (
                    "management_status",
                    models.CharField(
                        choices=[
                            ("waiting_part", "Esperando repuesto"),
                            ("waiting_pickup", "Esperando retiro"),
                            ("in_repair", "En reparacion"),
                            ("resolved", "Resuelto"),
                            ("pending_review", "Revision pendiente"),
                            ("unknown", "Desconocido"),
                        ],
                        default="unknown",
                        max_length=24,
                    ),
                ),
                ("incident_type", models.CharField(blank=True, default="", max_length=100)),
                ("summary", models.TextField(blank=True, default="")),
                ("location", models.CharField(blank=True, default="", max_length=255)),
                ("diagnosis", models.TextField(blank=True, default="")),
                ("pending", models.TextField(blank=True, default="")),
                ("responsible", models.CharField(blank=True, default="", max_length=255)),
                ("source_system", models.CharField(blank=True, default="", max_length=100)),
                ("proposal_key", models.CharField(max_length=128, unique=True)),
                ("opened_at", models.DateTimeField(db_index=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-opened_at", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="FgpyEquipmentAlias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("organization_key", models.CharField(db_index=True, default="forestal-paraguay", max_length=64)),
                ("fgpy_equipment_external_id", models.CharField(db_index=True, max_length=64)),
                ("alias", models.CharField(max_length=255)),
                ("normalized_alias", models.CharField(db_index=True, max_length=255)),
                ("confirmed", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["alias"],
            },
        ),
        migrations.CreateModel(
            name="FgpyMaintenanceEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("opened", "Apertura"),
                            ("update", "Actualizacion"),
                            ("diagnosis", "Diagnostico"),
                            ("status_change", "Cambio de estado"),
                            ("resolved", "Resolucion"),
                            ("cancelled", "Cancelacion"),
                            ("evidence", "Evidencia"),
                        ],
                        db_index=True,
                        default="update",
                        max_length=32,
                    ),
                ),
                ("description", models.TextField(blank=True, default="")),
                (
                    "operational_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("stopped", "Parada"),
                            ("operating", "Operando"),
                            ("intermittent", "Intermitente"),
                            ("unknown", "Desconocido"),
                        ],
                        max_length=24,
                        null=True,
                    ),
                ),
                (
                    "management_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("waiting_part", "Esperando repuesto"),
                            ("waiting_pickup", "Esperando retiro"),
                            ("in_repair", "En reparacion"),
                            ("resolved", "Resuelto"),
                            ("pending_review", "Revision pendiente"),
                            ("unknown", "Desconocido"),
                        ],
                        max_length=24,
                        null=True,
                    ),
                ),
                ("occurred_at", models.DateTimeField(db_index=True)),
                ("source_message_id", models.CharField(blank=True, default="", max_length=255)),
                ("source_group_key", models.CharField(blank=True, default="", max_length=100)),
                ("source_group_name", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "incident",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="fgpy_mantenimiento.fgpymaintenanceincident",
                    ),
                ),
            ],
            options={
                "ordering": ["occurred_at", "id"],
            },
        ),
        migrations.CreateModel(
            name="FgpyMaintenanceEvidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "evidence_type",
                    models.CharField(
                        choices=[
                            ("image", "Imagen"),
                            ("audio", "Audio"),
                            ("document", "Documento"),
                            ("message", "Mensaje"),
                            ("other", "Otra"),
                        ],
                        default="other",
                        max_length=32,
                    ),
                ),
                ("description", models.TextField(blank=True, default="")),
                ("external_reference", models.TextField(blank=True, default="")),
                ("mime_type", models.CharField(blank=True, default="", max_length=100)),
                ("size", models.PositiveBigIntegerField(blank=True, null=True)),
                ("sha256", models.CharField(blank=True, default="", max_length=64)),
                ("source_message_id", models.CharField(blank=True, default="", max_length=255)),
                ("source_group_key", models.CharField(blank=True, default="", max_length=100)),
                ("source_group_name", models.CharField(blank=True, default="", max_length=255)),
                ("captured_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "event",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="evidence",
                        to="fgpy_mantenimiento.fgpymaintenanceevent",
                    ),
                ),
                (
                    "incident",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evidence",
                        to="fgpy_mantenimiento.fgpymaintenanceincident",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at", "id"],
            },
        ),
        migrations.AddIndex(
            model_name="fgpymaintenanceincident",
            index=models.Index(fields=["organization_key", "status"], name="fgpy_maint_inc_org_status_idx"),
        ),
        migrations.AddIndex(
            model_name="fgpymaintenanceincident",
            index=models.Index(fields=["organization_key", "fgpy_equipment_external_id"], name="fgpy_maint_inc_org_equip_idx"),
        ),
        migrations.AddConstraint(
            model_name="fgpymaintenanceincident",
            constraint=models.CheckConstraint(
                check=models.Q(("organization_key", "forestal-paraguay")),
                name="fgpy_maint_incident_org_check",
            ),
        ),
        migrations.AddConstraint(
            model_name="fgpyequipmentalias",
            constraint=models.CheckConstraint(
                check=models.Q(("organization_key", "forestal-paraguay")),
                name="fgpy_maint_alias_org_check",
            ),
        ),
        migrations.AddConstraint(
            model_name="fgpyequipmentalias",
            constraint=models.UniqueConstraint(
                fields=("organization_key", "fgpy_equipment_external_id", "normalized_alias"),
                name="fgpy_maint_alias_identity_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="fgpymaintenanceevent",
            index=models.Index(fields=["source_group_key", "occurred_at"], name="fgpy_maint_evt_group_time_idx"),
        ),
        migrations.AddIndex(
            model_name="fgpymaintenanceevidence",
            index=models.Index(fields=["sha256"], name="fgpy_maint_evid_sha_idx"),
        ),
    ]
