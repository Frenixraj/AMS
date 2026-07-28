"""
Seed demo users for multi-role testing.

  python manage.py seed_demo_users --settings=config.settings_local
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from employees.models import Department, Employee

User = get_user_model()

DEMO_PASSWORD = "Demo1234!"

USERS = [
    {
        "email": "admin@assetflow.local",
        "username": "admin",
        "role": "ADMIN",
        "first_name": "Ada",
        "last_name": "Admin",
        "is_superuser": True,
        "employee_code": None,
        "phone": "+91-9000000001",
        "address": "Admin Office, HQ",
    },
    {
        "email": "assetmanager@assetflow.local",
        "username": "asset.manager",
        "role": "ASSET_MANAGER",
        "first_name": "Ash",
        "last_name": "Manager",
        "is_superuser": False,
        "employee_code": "AM001",
        "phone": "+91-9000000002",
        "address": "IT Store Room",
    },
    {
        "email": "manager@assetflow.local",
        "username": "manager",
        "role": "MANAGER",
        "first_name": "Maya",
        "last_name": "Manager",
        "is_superuser": False,
        "employee_code": "MGR001",
        "phone": "+91-9000000003",
        "address": "Engineering Floor",
    },
    {
        "email": "employee@assetflow.local",
        "username": "employee",
        "role": "EMPLOYEE",
        "first_name": "Eli",
        "last_name": "Employee",
        "is_superuser": False,
        "employee_code": "EMP001",
        "phone": "+91-9000000004",
        "address": "Cubicle 12",
    },
]


class Command(BaseCommand):
    help = "Create demo Admin / Asset Manager / Manager / Employee users."

    def handle(self, *args, **options):
        # Demote any legacy IT so Asset Manager slot is free
        User.objects.filter(role="IT_TEAM").update(role="EMPLOYEE")
        User.objects.filter(role="ASSET_MANAGER").exclude(
            email="assetmanager@assetflow.local"
        ).update(role="EMPLOYEE", is_active=False)

        dept, _ = Department.objects.get_or_create(
            code="ENG",
            defaults={"name": "Engineering", "description": "Demo department"},
        )

        created = []
        for spec in USERS:
            user, was_created = User.objects.get_or_create(
                email=spec["email"],
                defaults={
                    "username": spec["username"],
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "role": spec["role"],
                    "phone": spec.get("phone", ""),
                    "address": spec.get("address", ""),
                    "is_staff": True,
                    "is_superuser": spec["is_superuser"],
                },
            )
            user.set_password(DEMO_PASSWORD)
            user.role = spec["role"]
            user.phone = spec.get("phone", "")
            user.address = spec.get("address", "")
            user.is_staff = True
            user.is_superuser = spec["is_superuser"]
            user.is_active = True
            user.save()

            if spec["employee_code"]:
                Employee.objects.update_or_create(
                    user=user,
                    defaults={
                        "department": dept,
                        "employee_code": spec["employee_code"],
                        "job_title": spec["role"].replace("_", " ").title(),
                        "phone": spec.get("phone", ""),
                        "is_active": True,
                    },
                )

            if spec["role"] == "MANAGER":
                dept.manager = user
                dept.save(update_fields=["manager", "updated_at"])

            created.append(f"{spec['email']} ({spec['role']})")
            self.stdout.write(
                self.style.SUCCESS(
                    f"{'Created' if was_created else 'Updated'}: {spec['email']}"
                )
            )

        self.stdout.write("")
        self.stdout.write(self.style.WARNING(f"Password for all demo users: {DEMO_PASSWORD}"))
        self.stdout.write("Accounts: " + ", ".join(created))
        self.stdout.write("Admin notify email: frenixraj@gmail.com")
