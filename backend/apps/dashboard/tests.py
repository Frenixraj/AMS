"""Tests for dashboard summary API."""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from assets.models import Asset, AssetAssignment, AssetCategory
from authentication.models import User
from common.models import AuditLog
from employees.models import Department, Employee


class DashboardSummaryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dash",
            email="dash@example.com",
            password="TestPass123!",
            role=User.Role.IT_TEAM,
        )
        self.category_a = AssetCategory.objects.create(name="Laptop", code="LAPTOP")
        self.category_b = AssetCategory.objects.create(name="Monitor", code="MONITOR")
        self.dept = Department.objects.create(name="Engineering", code="ENG")
        self.emp_user = User.objects.create_user(
            username="emp",
            email="emp@example.com",
            password="TestPass123!",
            role=User.Role.EMPLOYEE,
        )
        self.employee = Employee.objects.create(
            user=self.emp_user,
            department=self.dept,
            employee_code="E-DASH",
        )

        Asset.objects.create(
            asset_tag="D-1",
            name="Available Laptop",
            category=self.category_a,
            serial_number="SD-1",
            status=Asset.Status.AVAILABLE,
            warranty_expiry=timezone.localdate() + timedelta(days=30),
            created_by=self.user,
        )
        allocated = Asset.objects.create(
            asset_tag="D-2",
            name="Allocated Laptop",
            category=self.category_a,
            serial_number="SD-2",
            status=Asset.Status.ALLOCATED,
            created_by=self.user,
        )
        Asset.objects.create(
            asset_tag="D-3",
            name="Lost Monitor",
            category=self.category_b,
            serial_number="SD-3",
            status=Asset.Status.LOST,
            created_by=self.user,
        )
        Asset.objects.create(
            asset_tag="D-4",
            name="In Repair",
            category=self.category_b,
            serial_number="SD-4",
            status=Asset.Status.MAINTENANCE,
            created_by=self.user,
        )
        AssetAssignment.objects.create(
            asset=allocated,
            employee=self.employee,
            assigned_by=self.user,
            assigned_at=timezone.now(),
            status=AssetAssignment.Status.ACTIVE,
        )
        AuditLog.objects.create(
            actor=self.user,
            action=AuditLog.Action.CREATE,
            entity_type="assets.Asset",
            entity_id=str(allocated.id),
            changes={"after": {"asset_tag": "D-2"}},
        )

    def test_summary_requires_auth(self):
        url = reverse("dashboard:summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_summary_widgets_and_charts(self):
        self.client.force_authenticate(self.user)
        url = reverse("dashboard:summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        widgets = response.data["widgets"]
        self.assertEqual(widgets["total_assets"], 4)
        self.assertEqual(widgets["available"], 1)
        self.assertEqual(widgets["allocated"], 1)
        self.assertEqual(widgets["maintenance"], 1)
        self.assertEqual(widgets["lost"], 1)
        self.assertEqual(widgets["warranty_expiring"], 1)

        categories = response.data["charts"]["category_distribution"]
        names = {row["name"]: row["value"] for row in categories}
        self.assertEqual(names["Laptop"], 2)
        self.assertEqual(names["Monitor"], 2)

        departments = response.data["charts"]["department_distribution"]
        self.assertEqual(departments[0]["name"], "Engineering")
        self.assertEqual(departments[0]["value"], 1)

        self.assertTrue(len(response.data["charts"]["monthly_allocations"]) >= 1)
        self.assertTrue(len(response.data["recent_activities"]) >= 1)
