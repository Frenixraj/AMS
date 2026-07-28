"""QR code generation for assets."""

from __future__ import annotations

import io

import qrcode
from django.core.files.base import ContentFile
from qrcode.image.pil import PilImage

from assets.models import Asset


def build_qr_payload(asset: Asset) -> str:
    """
    Canonical QR payload for scanning.
    Format is stable so future scanners can parse asset_tag reliably.
    """
    return f"ASSETFLOW:{asset.asset_tag}"


def generate_asset_qr_code(asset: Asset) -> Asset:
    """
    Generate a PNG QR image for the asset and save it to `asset.qr_code`.
    Replaces any existing QR file.
    """
    payload = build_qr_payload(asset)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    image: PilImage = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    filename = f"{asset.asset_tag}.png"
    if asset.qr_code:
        asset.qr_code.delete(save=False)

    asset.qr_code.save(filename, ContentFile(buffer.read()), save=False)
    asset.save(update_fields=["qr_code", "updated_at"])
    return asset
