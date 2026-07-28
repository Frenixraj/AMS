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
    },
    {
        "email": "it@assetflow.local",
        "username": "it.team",
        "role": "IT_TEAM",
        "first_name": "Ivan",
        "last_name": "IT",
        "is_superuser": False,
        "employee_code": "IT001",
    },
    {
        "email": "manager@assetflow.local",
        "username": "manager",
        "role": "MANAGER",
        "first_name": "Maya",
        "last_name": "Manager",
        "is_superuser": False,
        "employee_code": "MGR001",
    },
    {
        "email": "employee@assetflow.local",
        "username": "employee",
        "role": "EMPLOYEE",
        "first_name": "Eli",
        "last_name": "Employee",
        "is_superuser": False,
        "employee_code": "EMP001",
    },
]


class Command(BaseCommand):
    help = "Create demo Admin / IT / Manager / Employee users for local testing."

    def handle(self, *args, **options):
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
                    "is_staff": True,
                    "is_superuser": spec["is_superuser"],
                },
            )
            user.set_password(DEMO_PASSWORD)
            user.role = spec["role"]
            user.is_staff = True
            user.is_superuser = spec["is_superuser"]
            user.save()

            if spec["employee_code"]:
                Employee.objects.update_or_create(
                    user=user,
                    defaults={
                        "department": dept,
                        "employee_code": spec["employee_code"],
                        "job_title": spec["role"].replace("_", " ").title(),
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
