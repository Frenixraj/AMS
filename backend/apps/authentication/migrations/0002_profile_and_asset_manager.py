# Generated manually for profile fields + Asset Manager role migration

from django.db import migrations, models
import django.db.models.deletion


def migrate_it_to_asset_manager(apps, schema_editor):
    User = apps.get_model("authentication", "User")
    # Keep at most one active Asset Manager: convert first IT_TEAM, demote rest to EMPLOYEE.
    its = list(User.objects.filter(role="IT_TEAM").order_by("id"))
    if not its:
        return
    first = its[0]
    first.role = "ASSET_MANAGER"
    first.save(update_fields=["role"])
    for u in its[1:]:
        u.role = "EMPLOYEE"
        u.save(update_fields=["role"])


def noop_reverse(apps, schema_editor):
    User = apps.get_model("authentication", "User")
    User.objects.filter(role="ASSET_MANAGER").update(role="IT_TEAM")


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="phone",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.AddField(
            model_name="user",
            name="address",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="user",
            name="profile_picture",
            field=models.ImageField(blank=True, null=True, upload_to="profiles/%Y/%m/"),
        ),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("ADMIN", "Admin"),
                    ("ASSET_MANAGER", "Asset Manager"),
                    ("MANAGER", "Manager"),
                    ("EMPLOYEE", "Employee"),
                    ("IT_TEAM", "IT Team (legacy)"),
                ],
                db_index=True,
                default="EMPLOYEE",
                max_length=20,
            ),
        ),
        migrations.RunPython(migrate_it_to_asset_manager, noop_reverse),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_active", True), ("role", "ASSET_MANAGER")),
                fields=("role",),
                name="uq_one_active_asset_manager",
            ),
        ),
    ]
