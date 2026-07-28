import { useCallback, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { QrCameraScanner } from "@/components/assets/QrCameraScanner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { assetService } from "@/services/asset.service";
import { parseQrPayload } from "@/utils/qr";

/**
 * Camera scan page: decode QR → resolve asset → open Asset Details.
 */
export function QrScanPage() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [resolving, setResolving] = useState(false);
  const [manualPayload, setManualPayload] = useState("");
  const [scannerKey, setScannerKey] = useState(0);

  const resolveAndOpen = useCallback(
    async (decodedText: string) => {
      setError(null);
      setResolving(true);
      try {
        const parsed = parseQrPayload(decodedText);
        if (parsed.kind === "invalid") {
          setError(parsed.reason);
          setResolving(false);
          setScannerKey((k) => k + 1);
          return;
        }

        if (parsed.kind === "id") {
          navigate(`/assets/${parsed.assetId}`);
          return;
        }

        const asset = await assetService.getByTag(parsed.assetTag);
        navigate(`/assets/${asset.id}`);
      } catch {
        setError("No asset found for this QR code.");
        setResolving(false);
        setScannerKey((k) => k + 1);
      }
    },
    [navigate]
  );

  const handleManualSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    await resolveAndOpen(manualPayload);
  };

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <Link to="/assets" className="text-sm text-muted-foreground hover:text-foreground">
          ← Back to assets
        </Link>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">Scan QR</h1>
        <p className="text-sm text-muted-foreground">
          Scan an AssetFlow label to open the asset details page.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Camera</CardTitle>
          <CardDescription>
            Uses your device camera via html5-qrcode. HTTPS or localhost required.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {resolving ? (
            <p className="text-sm text-muted-foreground">Opening asset…</p>
          ) : (
            <QrCameraScanner key={scannerKey} onScan={resolveAndOpen} disabled={resolving} />
          )}
          {error && (
            <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Manual entry</CardTitle>
          <CardDescription>
            Paste a payload such as <span className="font-mono">ASSETFLOW:AST-001</span> if the
            camera is unavailable.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleManualSubmit} className="flex flex-col gap-3 sm:flex-row">
            <div className="flex-1 space-y-2">
              <Label htmlFor="manual-qr">QR payload</Label>
              <Input
                id="manual-qr"
                value={manualPayload}
                onChange={(e) => setManualPayload(e.target.value)}
                placeholder="ASSETFLOW:AST-001"
              />
            </div>
            <div className="flex items-end">
              <Button type="submit" disabled={resolving || !manualPayload.trim()}>
                Open asset
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
