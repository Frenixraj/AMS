"""Tests for Excel/PDF report exports."""

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from assets.models import Asset, AssetAssignment, AssetCategory
from authentication.models import User
from employees.models import Department, Employee
from maintenance.models import MaintenanceRecord


class ReportExportTests(APITestCase):
    def setUp(self):
        self.it = User.objects.create_user(
            username="itrep",
            email="itrep@example.com",
            password="TestPass123!",
            role=User.Role.IT_TEAM,
        )
        self.emp_user = User.objects.create_user(
            username="emprep",
            email="emprep@example.com",
            password="TestPass123!",
            role=User.Role.EMPLOYEE,
        )
        self.dept = Department.objects.create(name="Engineering", code="ENG")
        self.employee = Employee.objects.create(
            user=self.emp_user,
            department=self.dept,
            employee_code="E-REP",
        )
        self.category = AssetCategory.objects.create(name="Laptop", code="LAPTOP")
        self.asset = Asset.objects.create(
            asset_tag="R-1",
            name="Report Laptop",
            category=self.category,
            serial_number="SR-1",
            status=Asset.Status.ALLOCATED,
            created_by=self.it,
        )
        AssetAssignment.objects.create(
            asset=self.asset,
            employee=self.employee,
            assigned_by=self.it,
            assigned_at=timezone.now(),
            status=AssetAssignment.Status.ACTIVE,
        )
        MaintenanceRecord.objects.create(
            asset=self.asset,
            reported_by=self.employee,
            title="Fan noise",
            issue_description="Loud fan under load",
            status=MaintenanceRecord.Status.OPEN,
        )

    def test_excel_exports(self):
        self.client.force_authenticate(self.it)
        endpoints = [
            "reports:export-assets-by-department-xlsx",
            "reports:export-assets-by-category-xlsx",
            "reports:export-allocation-history-xlsx",
            "reports:export-maintenance-history-xlsx",
        ]
        for name in endpoints:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, status.HTTP_200_OK, name)
            self.assertIn(
                "spreadsheetml",
                response["Content-Type"],
                name,
            )
            self.assertTrue(response.content.startswith(b"PK"), name)  # zip/xlsx magic

    def test_pdf_exports(self):
        self.client.force_authenticate(self.it)
        endpoints = [
            "reports:export-assets-by-department-pdf",
            "reports:export-assets-by-category-pdf",
            "reports:export-allocation-history-pdf",
            "reports:export-maintenance-history-pdf",
        ]
        for name in endpoints:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, status.HTTP_200_OK, name)
            self.assertEqual(response["Content-Type"], "application/pdf", name)
            self.assertTrue(response.content.startswith(b"%PDF"), name)

    def test_employee_cannot_export(self):
        self.client.force_authenticate(self.emp_user)
        response = self.client.get(reverse("reports:export-assets-by-category-xlsx"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
