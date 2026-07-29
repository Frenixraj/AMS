/**
 * QR payload helpers.
 * Canonical encoded value: ASSETFLOW:{ASSET_TAG}
 */

export const QR_PREFIX = "ASSETFLOW:";

export function buildQrPayload(assetTag: string): string {
  return `${QR_PREFIX}${assetTag.trim().toUpperCase()}`;
}

/**
 * Extract an asset tag from a scanned QR string.
 * Accepts:
 * - ASSETFLOW:AST-001
 * - /assets/42 (numeric id path — returned as { kind: 'id' })
 * - full URLs containing /assets/:id
 */
export type ParsedQr =
  | { kind: "tag"; assetTag: string }
  | { kind: "id"; assetId: number }
  | { kind: "invalid"; reason: string };

export function parseQrPayload(raw: string): ParsedQr {
  const text = raw.trim();
  if (!text) {
    return { kind: "invalid", reason: "Empty QR payload." };
  }

  if (text.toUpperCase().startsWith(QR_PREFIX)) {
    const tag = text.slice(QR_PREFIX.length).trim().toUpperCase();
    if (!tag) {
      return { kind: "invalid", reason: "Missing asset tag in QR payload." };
    }
    return { kind: "tag", assetTag: tag };
  }

  // Deep-link style: .../assets/123 or /assets/123
  try {
    const asUrl = text.includes("://")
      ? new URL(text)
      : new URL(text, window.location.origin);
    const match = asUrl.pathname.match(/\/assets\/(\d+)\/?$/);
    if (match) {
      return { kind: "id", assetId: Number(match[1]) };
    }
  } catch {
    // not a URL — fall through
  }

  const pathMatch = text.match(/^\/?assets\/(\d+)\/?$/i);
  if (pathMatch) {
    return { kind: "id", assetId: Number(pathMatch[1]) };
  }

  // Bare tag fallback (scanned legacy labels)
  if (/^[A-Z0-9][A-Z0-9\-_/]{1,63}$/i.test(text)) {
    return { kind: "tag", assetTag: text.toUpperCase() };
  }

  return {
    kind: "invalid",
    reason: "Unrecognized QR format. Expected ASSETFLOW:{TAG}.",
  };
}

/** Prefer Vite-proxied /media path so downloads work without CORS issues. */
export function toProxiedMediaUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url, window.location.origin);
    if (parsed.pathname.startsWith("/media/")) {
      return `${parsed.pathname}${parsed.search}`;
    }
  } catch {
    if (url.startsWith("/media/")) return url;
  }
  return url;
}

export async function downloadQrImage(
  qrUrl: string,
  filename: string
): Promise<void> {
  const proxied = toProxiedMediaUrl(qrUrl) ?? qrUrl;
  const response = await fetch(proxied, { credentials: "include" });
  if (!response.ok) {
    throw new Error("Failed to download QR image.");
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename.endsWith(".png") ? filename : `${filename}.png`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}

export function printQrLabel(options: {
  assetTag: string;
  name: string;
  serialNumber: string;
  qrImageUrl: string;
  qrPayload: string;
  brandLogoUrl?: string;
}): void {
  const imageSrc = toProxiedMediaUrl(options.qrImageUrl) ?? options.qrImageUrl;
  const brandLogoUrl = options.brandLogoUrl ?? `${window.location.origin}/brand/logo.png`;
  const printWindow = window.open("", "_blank", "noopener,noreferrer,width=480,height=640");
  if (!printWindow) {
    throw new Error("Popup blocked. Allow popups to print QR labels.");
  }

  printWindow.document.write(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>QR Label — ${escapeHtml(options.assetTag)}</title>
  <style>
    @page { margin: 12mm; size: auto; }
    body {
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif;
      color: #111;
      margin: 0;
      padding: 16px;
    }
    .label {
      width: 320px;
      margin: 0 auto;
      border: 1px solid #111;
      padding: 16px;
      text-align: center;
      box-sizing: border-box;
    }
    .brand { margin: 0 auto 8px; }
    .brand img { width: 140px; height: auto; margin: 0 auto; display: block; }
    .tag { font-size: 22px; font-weight: 700; margin: 8px 0 4px; font-family: ui-monospace, monospace; }
    .name { font-size: 14px; margin-bottom: 4px; }
    .serial { font-size: 12px; color: #444; font-family: ui-monospace, monospace; }
    img.qr { width: 180px; height: 180px; margin: 12px auto; display: block; }
    .payload { font-size: 10px; word-break: break-all; color: #666; font-family: ui-monospace, monospace; }
  </style>
</head>
<body>
  <div class="label">
    <div class="brand"><img src="${escapeHtml(brandLogoUrl)}" alt="AssetFlow" onerror="this.parentElement.textContent='AssetFlow'" /></div>
    <div class="tag">${escapeHtml(options.assetTag)}</div>
    <div class="name">${escapeHtml(options.name)}</div>
    <div class="serial">S/N ${escapeHtml(options.serialNumber)}</div>
    <img class="qr" src="${escapeHtml(imageSrc)}" alt="QR ${escapeHtml(options.assetTag)}" />
    <div class="payload">${escapeHtml(options.qrPayload)}</div>
  </div>
  <script>
    const img = document.querySelector('img.qr');
    const triggerPrint = () => { window.focus(); window.print(); };
    if (img.complete) setTimeout(triggerPrint, 50);
    else img.onload = () => setTimeout(triggerPrint, 50);
    img.onerror = () => setTimeout(triggerPrint, 50);
  </script>
</body>
</html>`);
  printWindow.document.close();
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
