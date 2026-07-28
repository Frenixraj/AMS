import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { isAxiosError } from "axios";

import { AssetForm, type AssetFormSchema } from "@/components/assets/AssetForm";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import { assetService } from "@/services/asset.service";
import type { Asset, AssetCategory, Vendor } from "@/types/assets";

function canManageAssets(role?: string): boolean {
  return role === "ADMIN" || role === "ASSET_MANAGER" || role === "IT_TEAM";
}

function buildFormData(values: AssetFormSchema, imageFile: File | null): FormData {
  const formData = new FormData();
  formData.append("asset_tag", values.asset_tag.trim().toUpperCase());
  formData.append("name", values.name.trim());
  formData.append("category", String(values.category));
  formData.append("brand", values.brand ?? "");
  formData.append("model", values.model ?? "");
  formData.append("serial_number", values.serial_number.trim());
  formData.append("status", values.status);
  formData.append("notes", values.notes ?? "");
  if (values.purchase_date) formData.append("purchase_date", values.purchase_date);
  if (values.warranty_expiry) formData.append("warranty_expiry", values.warranty_expiry);
  if (values.purchase_cost) formData.append("purchase_cost", values.purchase_cost);
  if (values.vendor) formData.append("vendor", String(values.vendor));
  if (imageFile) formData.append("image", imageFile);
  return formData;
}

export function AssetFormPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const { user } = useAuth();
  const manage = canManageAssets(user?.role);

  const [categories, setCategories] = useState<AssetCategory[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [asset, setAsset] = useState<Asset | null>(null);
  const [loading, setLoading] = useState(isEdit);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!manage) {
      navigate("/assets", { replace: true });
    }
  }, [manage, navigate]);

  useEffect(() => {
    const load = async () => {
      try {
        const [categoryPage, vendorPage] = await Promise.all([
          assetService.listCategories(),
          assetService.listVendors(),
        ]);
        setCategories(categoryPage.results);
        setVendors(vendorPage.results);
        if (id) {
          const detail = await assetService.get(Number(id));
          setAsset(detail);
        }
      } catch {
        setError("Failed to load form data.");
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [id]);

  const handleSubmit = async (values: AssetFormSchema, imageFile: File | null) => {
    setSubmitting(true);
    setError(null);
    try {
      const formData = buildFormData(values, imageFile);
      const saved = isEdit
        ? await assetService.update(Number(id), formData)
        : await assetService.create(formData);
      navigate(`/assets/${saved.id}`);
    } catch (err) {
      if (isAxiosError(err) && err.response?.data) {
        const data = err.response.data as Record<string, unknown>;
        const messages = Object.entries(data)
          .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : String(value)}`)
          .join(" · ");
        setError(messages || "Validation failed.");
      } else {
        setError("Save failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading form…</p>;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <Link to="/assets" className="text-sm text-muted-foreground hover:text-foreground">
          ← Back to assets
        </Link>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">
          {isEdit ? "Edit asset" : "Add asset"}
        </h1>
        <p className="text-sm text-muted-foreground">
          QR codes are generated automatically on create and when the asset tag changes.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Asset details</CardTitle>
          <CardDescription>All fields are validated before save.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}
          {categories.length === 0 && !isEdit && (
            <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
              No categories yet — use “+ Add category” on the form below.
            </p>
          )}
          <AssetForm
            initial={asset}
            categories={categories}
            vendors={vendors}
            submitting={submitting}
            onSubmit={handleSubmit}
            onCancel={() => navigate(isEdit ? `/assets/${id}` : "/assets")}
            onCreateCategory={async (payload) => {
              const created = await assetService.createCategory(payload);
              setCategories((prev) =>
                [...prev, created].sort((a, b) => a.name.localeCompare(b.name))
              );
              return created;
            }}
            onCreateVendor={async (payload) => {
              const created = await assetService.createVendor(payload);
              setVendors((prev) =>
                [...prev, created].sort((a, b) => a.name.localeCompare(b.name))
              );
              return created;
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
}
