import { useEffect, useRef, useState } from "react";
import { Html5Qrcode, Html5QrcodeSupportedFormats } from "html5-qrcode";

import { Button } from "@/components/ui/button";

interface QrCameraScannerProps {
  onScan: (decodedText: string) => void;
  disabled?: boolean;
}

const SCANNER_ELEMENT_ID = "assetflow-qr-reader";

/**
 * Camera-based QR scanner using html5-qrcode.
 * Starts on mount; stops cleanly on unmount to release the camera.
 */
export function QrCameraScanner({ onScan, disabled = false }: QrCameraScannerProps) {
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const handledRef = useRef(false);
  const onScanRef = useRef(onScan);

  useEffect(() => {
    onScanRef.current = onScan;
  }, [onScan]);

  useEffect(() => {
    if (disabled) return;

    let cancelled = false;
    handledRef.current = false;
    const scanner = new Html5Qrcode(SCANNER_ELEMENT_ID, {
      formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
      verbose: false,
    });
    scannerRef.current = scanner;

    const start = async () => {
      try {
        setError(null);
        await scanner.start(
          { facingMode: "environment" },
          {
            fps: 10,
            qrbox: { width: 240, height: 240 },
            aspectRatio: 1,
          },
          (decodedText) => {
            if (handledRef.current || cancelled) return;
            handledRef.current = true;
            onScanRef.current(decodedText);
          },
          () => {
            // Ignore per-frame "not found" noise.
          }
        );
        if (!cancelled) setRunning(true);
      } catch (err) {
        if (cancelled) return;
        const message =
          err instanceof Error
            ? err.message
            : "Unable to access camera. Check browser permissions.";
        setError(message);
        setRunning(false);
      }
    };

    void start();

    return () => {
      cancelled = true;
      const active = scannerRef.current;
      scannerRef.current = null;
      if (!active) return;
      void (async () => {
        try {
          if (active.isScanning) {
            await active.stop();
          }
        } catch {
          // Camera may already be stopped.
        }
        try {
          active.clear();
        } catch {
          // Element may already be unmounted.
        }
      })();
    };
  }, [disabled]);

  return (
    <div className="space-y-3" role="region" aria-label="QR camera scanner">
      <div
        id={SCANNER_ELEMENT_ID}
        className="overflow-hidden rounded-lg border bg-black/90 [&_video]:mx-auto [&_video]:max-h-[360px] [&_video]:w-full [&_video]:object-cover"
      />
      {error && (
        <p
          className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive"
          role="alert"
        >
          {error}
        </p>
      )}
      <p className="text-xs text-muted-foreground" aria-live="polite">
        {running
          ? "Point the camera at an AssetFlow QR label."
          : "Starting camera…"}
      </p>
      {error && (
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => window.location.reload()}
        >
          Retry camera
        </Button>
      )}
    </div>
  );
}
