import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { downloadQrImage, printQrLabel, toProxiedMediaUrl } from "@/utils/qr";

interface AssetQrPanelProps {
  assetTag: string;
  name: string;
  serialNumber: string;
  qrPayload: string;
  qrCodeUrl: string | null;
  canRegenerate?: boolean;
  regenerating?: boolean;
  onRegenerate?: () => void;
}

export function AssetQrPanel({
  assetTag,
  name,
  serialNumber,
  qrPayload,
  qrCodeUrl,
  canRegenerate = false,
  regenerating = false,
  onRegenerate,
}: AssetQrPanelProps) {
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const displayUrl = toProxiedMediaUrl(qrCodeUrl);

  const handleDownload = async () => {
    if (!qrCodeUrl) return;
    setBusy(true);
    setActionError(null);
    try {
      await downloadQrImage(qrCodeUrl, `${assetTag}-qr.png`);
    } catch {
      setActionError("Download failed. Try regenerating the QR code.");
    } finally {
      setBusy(false);
    }
  };

  const handlePrint = () => {
    if (!qrCodeUrl) return;
    setActionError(null);
    try {
      printQrLabel({
        assetTag,
        name,
        serialNumber,
        qrImageUrl: qrCodeUrl,
        qrPayload,
      });
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Unable to open print dialog."
      );
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">QR code</CardTitle>
        <CardDescription className="font-mono text-xs">{qrPayload}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {displayUrl ? (
          <img
            src={displayUrl}
            alt={`QR for ${assetTag}`}
            className="mx-auto max-h-48 rounded-md border bg-white p-2"
          />
        ) : (
          <p className="text-sm text-muted-foreground">QR not generated yet.</p>
        )}

        {actionError && (
          <p className="text-xs text-destructive">{actionError}</p>
        )}

        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={!qrCodeUrl || busy}
            onClick={handleDownload}
          >
            Download QR
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={!qrCodeUrl || busy}
            onClick={handlePrint}
          >
            Print label
          </Button>
          {canRegenerate && onRegenerate && (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled={regenerating || busy}
              onClick={onRegenerate}
            >
              {regenerating ? "Regenerating…" : "Regenerate QR"}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
