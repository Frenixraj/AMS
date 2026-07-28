"""Smoke tests for remaining plan modules."""

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from assets.models import Asset, AssetAssignment, AssetCategory
from assets.services.assignment import assign_asset
from authentication.models import User
from employees.models import Department, Employee
from maintenance.models import MaintenanceRecord
from notifications.models import Notification


class EmployeesAPITests(APITestCase):
    def setUp(self):
        self.it = User.objects.create_user(
            username="it", email="it@ex.com", password="x", role=User.Role.IT_TEAM
        )
        self.mgr = User.objects.create_user(
            username="mgr", email="mgr@ex.com", password="x", role=User.Role.MANAGER
        )
        self.emp_user = User.objects.create_user(
            username="emp", email="emp@ex.com", password="x", role=User.Role.EMPLOYEE
        )
        self.dept = Department.objects.create(name="Ops", code="OPS", manager=self.mgr)

    def test_create_department_and_employee(self):
        self.client.force_authenticate(self.it)
        dept_resp = self.client.post(
            reverse("employees:department-list"),
            {"name": "Finance", "code": "FIN", "description": "Finance dept"},
            format="json",
        )
        self.assertEqual(dept_resp.status_code, status.HTTP_201_CREATED, dept_resp.data)
        emp_resp = self.client.post(
            reverse("employees:employee-list"),
            {
                "user": self.emp_user.id,
                "department": dept_resp.data["id"],
                "employee_code": "E-100",
                "job_title": "Analyst",
            },
            format="json",
        )
        self.assertEqual(emp_resp.status_code, status.HTTP_201_CREATED, emp_resp.data)


class AssignmentAPITests(APITestCase):
    def setUp(self):
        self.it = User.objects.create_user(
            username="it2", email="it2@ex.com", password="x", role=User.Role.IT_TEAM
        )
        self.emp_user = User.objects.create_user(
            username="emp2", email="emp2@ex.com", password="x", role=User.Role.EMPLOYEE
        )
        self.dept = Department.objects.create(name="HR", code="HR")
        self.employee = Employee.objects.create(
            user=self.emp_user, department=self.dept, employee_code="E-200"
        )
        self.category = AssetCategory.objects.create(name="Phone", code="PHONE")
        self.asset = Asset.objects.create(
            asset_tag="P-1",
            name="iPhone",
            category=self.category,
            serial_number="SP-1",
            status=Asset.Status.AVAILABLE,
            created_by=self.it,
        )

    def test_assign_and_return(self):
        self.client.force_authenticate(self.it)
        assign = self.client.post(
            reverse("asset-assignment-assign"),
            {"asset_id": self.asset.id, "employee_id": self.employee.id},
            format="json",
        )
        self.assertEqual(assign.status_code, status.HTTP_201_CREATED, assign.data)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.ALLOCATED)
        ret = self.client.post(
            reverse("asset-assignment-return-asset", args=[assign.data["id"]]),
            {"notes": "Returned"},
            format="json",
        )
        self.assertEqual(ret.status_code, status.HTTP_200_OK, ret.data)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.AVAILABLE)


class MaintenanceNotificationsReportsTests(APITestCase):
    def setUp(self):
        self.it = User.objects.create_user(
            username="it3", email="it3@ex.com", password="x", role=User.Role.IT_TEAM
        )
        self.emp_user = User.objects.create_user(
            username="emp3", email="emp3@ex.com", password="x", role=User.Role.EMPLOYEE
        )
        self.dept = Department.objects.create(name="Sales", code="SAL")
        self.employee = Employee.objects.create(
            user=self.emp_user, department=self.dept, employee_code="E-300"
        )
        self.category = AssetCategory.objects.create(name="Laptop", code="LAP")
        self.asset = Asset.objects.create(
            asset_tag="L-1",
            name="ThinkPad",
            category=self.category,
            serial_number="SL-1",
            status=Asset.Status.AVAILABLE,
            created_by=self.it,
        )

    def test_maintenance_create_and_complete(self):
        # Employee must own the asset before raising maintenance
        assign_asset(
            asset_id=self.asset.id,
            employee_id=self.employee.id,
            actor=self.it,
        )
        self.client.force_authenticate(self.emp_user)
        created = self.client.post(
            reverse("maintenance:maintenance-ticket-list"),
            {
                "asset": self.asset.id,
                "title": "Screen flicker",
                "issue_description": "Display flickers under load",
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        self.assertEqual(created.data["status"], "PENDING_APPROVAL")
        self.asset.refresh_from_db()
        # Asset stays ALLOCATED until maintenance is approved
        self.assertEqual(self.asset.status, Asset.Status.ALLOCATED)

        # Admin/manager approve
        admin = User.objects.create_user(
            username="adm3", email="adm3@ex.com", password="x", role=User.Role.ADMIN
        )
        self.client.force_authenticate(admin)
        approved = self.client.post(
            reverse("maintenance:maintenance-ticket-approve", args=[created.data["id"]]),
            {},
            format="json",
        )
        self.assertEqual(approved.status_code, status.HTTP_200_OK, approved.data)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.MAINTENANCE)

        self.client.force_authenticate(self.it)
        done = self.client.post(
            reverse("maintenance:maintenance-ticket-complete", args=[created.data["id"]]),
            {"resolution_notes": "Replaced cable"},
            format="json",
        )
        self.assertEqual(done.status_code, status.HTTP_200_OK, done.data)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.ALLOCATED)

    def test_notifications_unread_and_mark_read(self):
        Notification.objects.create(
            recipient=self.emp_user,
            title="Hello",
            message="World",
            notification_type=Notification.NotificationType.INFO,
        )
        self.client.force_authenticate(self.emp_user)
        count = self.client.get(reverse("notifications:notification-unread-count"))
        self.assertEqual(count.status_code, status.HTTP_200_OK)
        self.assertEqual(count.data["unread_count"], 1)
        listed = self.client.get(reverse("notifications:notification-list"))
        notif_id = listed.data["results"][0]["id"]
        marked = self.client.post(
            reverse("notifications:notification-mark-read", args=[notif_id])
        )
        self.assertEqual(marked.status_code, status.HTTP_200_OK)
        self.assertTrue(marked.data["is_read"])

    def test_reports_inventory(self):
        self.client.force_authenticate(self.it)
        resp = self.client.get(reverse("reports:inventory"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data["total"], 1)
