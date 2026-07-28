"""
Asset master data: categories, vendors, assets, and assignment history.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from common.models import TimeStampedModel


class AssetCategory(TimeStampedModel):
    """Taxonomy for assets (Laptop, Monitor, Phone, …)."""

    name = models.CharField(max_length=80, unique=True)
    code = models.CharField(max_length=32, unique=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "asset category"
        verbose_name_plural = "asset categories"

    def __str__(self) -> str:
        return self.name


class Vendor(TimeStampedModel):
    """Supplier / OEM used at purchase time."""

    name = models.CharField(max_length=160, unique=True)
    contact_person = models.CharField(max_length=120, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    address = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "name"], name="idx_vendor_active_name"),
        ]
        verbose_name = "vendor"
        verbose_name_plural = "vendors"

    def __str__(self) -> str:
        return self.name


class Asset(TimeStampedModel):
    """Physical or logical IT asset tracked through its lifecycle."""

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        REQUESTED = "REQUESTED", "Requested"
        ALLOCATED = "ALLOCATED", "Allocated"
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        RETIRED = "RETIRED", "Retired"
        LOST = "LOST", "Lost"

    asset_tag = models.CharField(
        max_length=64,
        unique=True,
        help_text="Business asset ID shown on labels / QR payloads.",
    )
    name = models.CharField(max_length=160)
    category = models.ForeignKey(
        AssetCategory,
        on_delete=models.PROTECT,
        related_name="assets",
    )
    brand = models.CharField(max_length=80, blank=True, default="")
    model = models.CharField(max_length=80, blank=True, default="")
    serial_number = models.CharField(max_length=120, unique=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
    )
    warranty_expiry = models.DateField(null=True, blank=True, db_index=True)
    qr_code = models.ImageField(
        upload_to="qr_codes/",
        blank=True,
        null=True,
        help_text="Generated QR image file (local media).",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
    )
    image = models.ImageField(upload_to="assets/", blank=True, null=True)
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_assets",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "category"], name="idx_asset_status_cat"),
            models.Index(fields=["brand", "model"], name="idx_asset_brand_model"),
            models.Index(fields=["vendor", "status"], name="idx_asset_vendor_status"),
        ]
        verbose_name = "asset"
        verbose_name_plural = "assets"
        constraints = [
            models.CheckConstraint(
                check=models.Q(purchase_cost__isnull=True)
                | models.Q(purchase_cost__gte=0),
                name="chk_asset_purchase_cost_nonneg",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.asset_tag} — {self.name}"


class AssetAssignment(TimeStampedModel):
    """
    History of who held an asset.
    At most one ACTIVE assignment per asset (enforced by partial unique constraint).
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        RETURNED = "RETURNED", "Returned"
        LOST = "LOST", "Lost"

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asset_assignments_made",
    )
    assigned_at = models.DateTimeField(db_index=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-assigned_at"]
        indexes = [
            models.Index(fields=["employee", "status"], name="idx_assign_emp_status"),
            models.Index(fields=["asset", "status"], name="idx_assign_asset_status"),
        ]
        constraints = [
            # Only one active holder per asset at a time (PostgreSQL partial unique).
            models.UniqueConstraint(
                fields=["asset"],
                condition=models.Q(status="ACTIVE"),
                name="uq_asset_one_active_assignment",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(returned_at__isnull=True)
                    | models.Q(returned_at__gte=models.F("assigned_at"))
                ),
                name="chk_assign_return_after_assign",
            ),
        ]
        verbose_name = "asset assignment"
        verbose_name_plural = "asset assignments"

    def __str__(self) -> str:
        return f"{self.asset.asset_tag} → {self.employee.employee_code} ({self.status})"
