from django.db import migrations, models


CONSTRAINT_NAMES = (
    "forestal_fgpy_driver_proposal_uniq",
    "forestal_fgpy_vehicle_plate_confirmed_uniq",
    "forestal_fgpy_vehicle_proposal_uniq",
)


def normalize_unique_keys(apps, schema_editor):
    Driver = apps.get_model("forestal_bot", "FgpyDriver")
    Vehicle = apps.get_model("forestal_bot", "FgpyVehicle")
    Driver.objects.filter(proposal_key="").update(proposal_key=None)
    Vehicle.objects.filter(proposal_key="").update(proposal_key=None)
    for vehicle in Vehicle.objects.filter(status="confirmed").exclude(normalized_plate=""):
        vehicle.confirmed_plate_key = vehicle.normalized_plate
        vehicle.save(update_fields=["confirmed_plate_key"])


def remove_existing_conditional_constraints(apps, schema_editor):
    for model_name in ("FgpyDriver", "FgpyVehicle"):
        model = apps.get_model("forestal_bot", model_name)
        with schema_editor.connection.cursor() as cursor:
            existing = schema_editor.connection.introspection.get_constraints(
                cursor, model._meta.db_table
            )
        for constraint in model._meta.constraints:
            if constraint.name in CONSTRAINT_NAMES and constraint.name in existing:
                schema_editor.remove_constraint(model, constraint)


class Migration(migrations.Migration):
    dependencies = [("forestal_bot", "0009_fgpydriver_fgpyvehicle_fuelreport_fuelreportevidence_and_more")]

    operations = [
        migrations.AddField(
            model_name="fgpyvehicle",
            name="confirmed_plate_key",
            field=models.CharField(blank=True, default=None, editable=False, max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name="fgpydriver",
            name="proposal_key",
            field=models.CharField(blank=True, default=None, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name="fgpyvehicle",
            name="proposal_key",
            field=models.CharField(blank=True, default=None, max_length=128, null=True),
        ),
        migrations.RunPython(normalize_unique_keys, migrations.RunPython.noop),
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(remove_existing_conditional_constraints, migrations.RunPython.noop)],
            state_operations=[
                migrations.RemoveConstraint(model_name="fgpydriver", name="forestal_fgpy_driver_proposal_uniq"),
                migrations.RemoveConstraint(model_name="fgpyvehicle", name="forestal_fgpy_vehicle_plate_confirmed_uniq"),
                migrations.RemoveConstraint(model_name="fgpyvehicle", name="forestal_fgpy_vehicle_proposal_uniq"),
            ],
        ),
        migrations.AddConstraint(
            model_name="fgpydriver",
            constraint=models.UniqueConstraint(fields=("organization_key", "proposal_key"), name="forestal_fgpy_driver_proposal_uniq"),
        ),
        migrations.AddConstraint(
            model_name="fgpyvehicle",
            constraint=models.UniqueConstraint(fields=("organization_key", "confirmed_plate_key"), name="forestal_fgpy_vehicle_plate_confirmed_uniq"),
        ),
        migrations.AddConstraint(
            model_name="fgpyvehicle",
            constraint=models.UniqueConstraint(fields=("organization_key", "proposal_key"), name="forestal_fgpy_vehicle_proposal_uniq"),
        ),
    ]
