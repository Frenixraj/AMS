"""Tests for approval workflow API."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from approvals.models import Approval, AssetRequest
from assets.models import Asset, AssetAssignment, AssetCategory
from authentication.models import User
from common.models import AuditLog
from employees.models import Department, Employee
from notifications.models import Notification


class ApprovalWorkflowTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="TestPass123!",
            role=User.Role.ADMIN,
        )
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="TestPass123!",
            role=User.Role.MANAGER,
        )
        self.it_user = User.objects.create_user(
            username="it",
            email="it@example.com",
            password="TestPass123!",
            role=User.Role.IT_TEAM,
        )
        self.emp_user = User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="TestPass123!",
            role=User.Role.EMPLOYEE,
        )
        self.department = Department.objects.create(
            name="Engineering",
            code="ENG",
            manager=self.manager,
        )
        self.employee = Employee.objects.create(
            user=self.emp_user,
            department=self.department,
            employee_code="E-001",
        )
        self.category = AssetCategory.objects.create(name="Laptop", code="LAPTOP")
        self.asset = Asset.objects.create(
            asset_tag="AST-REQ-1",
            name="Dell Latitude",
            category=self.category,
            serial_number="SN-REQ-1",
            status=Asset.Status.AVAILABLE,
            created_by=self.it_user,
        )

    def test_employee_request_manager_approve_it_fulfill(self):
        self.client.force_authenticate(self.emp_user)
        create_url = reverse("asset-request-list")
        response = self.client.post(
            create_url,
            {
                "category": self.category.id,
                "asset": self.asset.id,
                "justification": "Need a laptop for project work.",
                "priority": "HIGH",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        request_id = response.data["id"]
        self.assertEqual(response.data["status"], "PENDING")
        self.assertTrue(len(response.data["timeline"]) >= 2)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.REQUESTED)
        self.assertTrue(
            AuditLog.objects.filter(
                entity_type="approvals.AssetRequest",
                entity_id=str(request_id),
                action=AuditLog.Action.CREATE,
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(recipient=self.manager).exists()
        )

        self.client.force_authenticate(self.manager)
        approve_url = reverse("asset-request-approve", args=[request_id])
        response = self.client.post(approve_url, {"comments": "Approved for Q1"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        # Approve now assigns immediately when a specific asset was requested
        self.assertEqual(response.data["status"], "FULFILLED")
        self.assertEqual(
            Approval.objects.get(asset_request_id=request_id).decision,
            Approval.Decision.APPROVED,
        )
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.ALLOCATED)
        self.assertTrue(
            AssetAssignment.objects.filter(
                asset=self.asset,
                employee=self.employee,
                status=AssetAssignment.Status.ACTIVE,
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                entity_id=str(request_id),
                action=AuditLog.Action.ASSIGN,
            ).exists()
        )

    def test_manager_can_reject(self):
        self.client.force_authenticate(self.emp_user)
        created = self.client.post(
            reverse("asset-request-list"),
            {
                "asset": self.asset.id,
                "justification": "Need this specific device urgently.",
                "priority": "MEDIUM",
            },
            format="json",
        )
        request_id = created.data["id"]

        self.client.force_authenticate(self.manager)
        response = self.client.post(
            reverse("asset-request-reject", args=[request_id]),
            {"comments": "Budget freeze"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "REJECTED")
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.AVAILABLE)

    def test_employee_without_profile_forbidden(self):
        bare = User.objects.create_user(
            username="bare",
            email="bare@example.com",
            password="TestPass123!",
            role=User.Role.EMPLOYEE,
        )
        self.client.force_authenticate(bare)
        response = self.client.post(
            reverse("asset-request-list"),
            {
                "category": self.category.id,
                "justification": "I should not be able to request.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
