"""Tests for Asset Management API."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from assets.models import Asset, AssetCategory, Vendor
from assets.services.qr import build_qr_payload
from authentication.models import User
from common.models import AuditLog


class AssetAPITestCase(APITestCase):
    def setUp(self):
        self.it_user = User.objects.create_user(
            username="it.user",
            email="it@example.com",
            password="TestPass123!",
            role=User.Role.IT_TEAM,
        )
        self.employee = User.objects.create_user(
            username="emp.user",
            email="emp@example.com",
            password="TestPass123!",
            role=User.Role.EMPLOYEE,
        )
        self.category = AssetCategory.objects.create(
            name="Laptop",
            code="LAPTOP",
        )
        self.vendor = Vendor.objects.create(name="Acme Hardware")

    def _auth(self, user: User) -> None:
        self.client.force_authenticate(user=user)

    def test_it_can_create_asset_with_qr_and_audit(self):
        self._auth(self.it_user)
        url = reverse("asset-list")
        payload = {
            "asset_tag": "AST-001",
            "name": "MacBook Pro 14",
            "category": self.category.id,
            "brand": "Apple",
            "model": "M3",
            "serial_number": "SN-MAC-001",
            "vendor": self.vendor.id,
            "status": Asset.Status.AVAILABLE,
            "purchase_cost": "1999.00",
        }
        response = self.client.post(url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        asset = Asset.objects.get(asset_tag="AST-001")
        self.assertTrue(asset.qr_code)
        self.assertEqual(build_qr_payload(asset), "ASSETFLOW:AST-001")
        self.assertTrue(
            AuditLog.objects.filter(
                entity_type="assets.Asset",
                entity_id=str(asset.pk),
                action=AuditLog.Action.CREATE,
            ).exists()
        )

    def test_employee_cannot_create_asset(self):
        self._auth(self.employee)
        url = reverse("asset-list")
        response = self.client.post(
            url,
            {
                "asset_tag": "AST-002",
                "name": "Monitor",
                "category": self.category.id,
                "serial_number": "SN-MON-001",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_filter_search_and_pagination(self):
        self._auth(self.it_user)
        Asset.objects.create(
            asset_tag="AST-100",
            name="Dell XPS",
            category=self.category,
            serial_number="SN-100",
            brand="Dell",
            status=Asset.Status.AVAILABLE,
            created_by=self.it_user,
        )
        Asset.objects.create(
            asset_tag="AST-200",
            name="HP Elite",
            category=self.category,
            serial_number="SN-200",
            brand="HP",
            status=Asset.Status.ALLOCATED,
            created_by=self.it_user,
        )

        self._auth(self.employee)
        list_url = reverse("asset-list")
        filtered = self.client.get(list_url, {"status": "AVAILABLE"})
        self.assertEqual(filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(filtered.data["count"], 1)
        self.assertEqual(filtered.data["results"][0]["asset_tag"], "AST-100")

        searched = self.client.get(list_url, {"search": "Elite"})
        self.assertEqual(searched.data["count"], 1)
        self.assertEqual(searched.data["results"][0]["asset_tag"], "AST-200")

    def test_update_status_writes_audit(self):
        self._auth(self.it_user)
        asset = Asset.objects.create(
            asset_tag="AST-300",
            name="Keyboard",
            category=self.category,
            serial_number="SN-300",
            status=Asset.Status.AVAILABLE,
            created_by=self.it_user,
        )
        url = reverse("asset-detail", args=[asset.pk])
        response = self.client.patch(
            url,
            {"status": Asset.Status.MAINTENANCE},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            AuditLog.objects.filter(
                entity_id=str(asset.pk),
                action=AuditLog.Action.STATUS_CHANGE,
            ).exists()
        )

    def test_image_upload(self):
        self._auth(self.it_user)
        from io import BytesIO

        from PIL import Image

        buffer = BytesIO()
        Image.new("RGB", (8, 8), color=(20, 120, 200)).save(buffer, format="PNG")
        image = SimpleUploadedFile(
            "laptop.png",
            buffer.getvalue(),
            content_type="image/png",
        )
        url = reverse("asset-list")
        response = self.client.post(
            url,
            {
                "asset_tag": "AST-IMG",
                "name": "Imaged Laptop",
                "category": self.category.id,
                "serial_number": "SN-IMG",
                "image": image,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        asset = Asset.objects.get(asset_tag="AST-IMG")
        self.assertTrue(asset.image)

    def test_regenerate_qr_endpoint(self):
        self._auth(self.it_user)
        asset = Asset.objects.create(
            asset_tag="AST-QR",
            name="Phone",
            category=self.category,
            serial_number="SN-QR",
            created_by=self.it_user,
        )
        url = reverse("asset-regenerate-qr", args=[asset.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        asset.refresh_from_db()
        self.assertTrue(asset.qr_code)

    def test_lookup_asset_by_tag_for_qr_scan(self):
        self._auth(self.employee)
        asset = Asset.objects.create(
            asset_tag="AST-SCAN",
            name="Scanner Target",
            category=self.category,
            serial_number="SN-SCAN",
            created_by=self.it_user,
        )
        url = reverse("asset-by-tag", kwargs={"asset_tag": "AST-SCAN"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], asset.id)
        self.assertEqual(response.data["asset_tag"], "AST-SCAN")
        self.assertEqual(response.data["qr_payload"], "ASSETFLOW:AST-SCAN")


    def test_validation_warranty_before_purchase(self):
        self._auth(self.it_user)
        url = reverse("asset-list")
        response = self.client.post(
            url,
            {
                "asset_tag": "AST-BAD",
                "name": "Bad Dates",
                "category": self.category.id,
                "serial_number": "SN-BAD",
                "purchase_date": "2024-06-01",
                "warranty_expiry": "2023-01-01",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("warranty_expiry", response.data)

    def test_illegal_status_transition_rejected(self):
        self._auth(self.it_user)
        asset = Asset.objects.create(
            asset_tag="AST-RET",
            name="Retired Gear",
            category=self.category,
            serial_number="SN-RET",
            status=Asset.Status.RETIRED,
            created_by=self.it_user,
        )
        url = reverse("asset-detail", kwargs={"pk": asset.pk})
        response = self.client.patch(
            url,
            {"status": Asset.Status.AVAILABLE},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)
