# Maintenance: pending approval status

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("maintenance", "0001_initial"),
        ("authentication", "0002_profile_and_asset_manager"),
    ]

    operations = [
        migrations.AlterField(
            model_name="maintenancerecord",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING_APPROVAL", "Pending Approval"),
                    ("OPEN", "Open"),
                    ("IN_PROGRESS", "In Progress"),
                    ("COMPLETED", "Completed"),
                    ("CANCELLED", "Cancelled"),
                    ("REJECTED", "Rejected"),
                ],
                db_index=True,
                default="PENDING_APPROVAL",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="maintenancerecord",
            name="assigned_to",
            field=models.ForeignKey(
                blank=True,
                help_text="Staff responsible for the ticket.",
                limit_choices_to={"role__in": ["ASSET_MANAGER", "ADMIN", "IT_TEAM"]},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_maintenance",
                to="authentication.user",
            ),
        ),
        migrations.AddField(
            model_name="maintenancerecord",
            name="approval_comments",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="maintenancerecord",
            name="decided_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="maintenance_decisions",
                to="authentication.user",
            ),
        ),
        migrations.AddField(
            model_name="maintenancerecord",
            name="decided_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
