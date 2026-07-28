import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState, type ReactNode } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { Asset, AssetCategory, AssetStatus, Vendor } from "@/types/assets";
import { ASSET_STATUSES } from "@/types/assets";

const assetFormSchema = z.object({
  asset_tag: z.string().min(1, "Asset tag is required").max(64),
  name: z.string().min(1, "Name is required").max(160),
  category: z.coerce.number().int().positive("Category is required"),
  brand: z.string().max(80).optional().default(""),
  model: z.string().max(80).optional().default(""),
  serial_number: z.string().min(1, "Serial number is required").max(120),
  purchase_date: z.string().optional().default(""),
  purchase_cost: z.string().optional().default(""),
  vendor: z.preprocess(
    (value) => (value === "" || value === null || value === undefined ? "" : Number(value)),
    z.union([z.number().int().positive(), z.literal("")])
  ),
  warranty_expiry: z.string().optional().default(""),
  status: z.enum([
    "AVAILABLE",
    "REQUESTED",
    "ALLOCATED",
    "MAINTENANCE",
    "RETIRED",
    "LOST",
  ]),
  notes: z.string().optional().default(""),
  image: z.any().optional(),
});

export type AssetFormSchema = z.infer<typeof assetFormSchema>;

interface AssetFormProps {
  initial?: Asset | null;
  categories: AssetCategory[];
  vendors: Vendor[];
  submitting?: boolean;
  onSubmit: (values: AssetFormSchema, imageFile: File | null) => Promise<void>;
  onCancel: () => void;
  onCreateCategory: (payload: {
    name: string;
    code: string;
    description?: string;
  }) => Promise<AssetCategory>;
  onCreateVendor: (payload: { name: string }) => Promise<Vendor>;
}

export function AssetForm({
  initial,
  categories,
  vendors,
  submitting = false,
  onSubmit,
  onCancel,
  onCreateCategory,
  onCreateVendor,
}: AssetFormProps) {
  const [showNewCategory, setShowNewCategory] = useState(false);
  const [showNewVendor, setShowNewVendor] = useState(false);
  const [newCategory, setNewCategory] = useState({ name: "", code: "" });
  const [newVendorName, setNewVendorName] = useState("");
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [lookupBusy, setLookupBusy] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm<AssetFormSchema>({
    resolver: zodResolver(assetFormSchema),
    defaultValues: {
      asset_tag: "",
      name: "",
      category: undefined as unknown as number,
      brand: "",
      model: "",
      serial_number: "",
      purchase_date: "",
      purchase_cost: "",
      vendor: "",
      warranty_expiry: "",
      status: "AVAILABLE",
      notes: "",
    },
  });

  useEffect(() => {
    if (!initial) return;
    reset({
      asset_tag: initial.asset_tag,
      name: initial.name,
      category: initial.category,
      brand: initial.brand ?? "",
      model: initial.model ?? "",
      serial_number: initial.serial_number,
      purchase_date: initial.purchase_date ?? "",
      purchase_cost: initial.purchase_cost ?? "",
      vendor: initial.vendor ?? "",
      warranty_expiry: initial.warranty_expiry ?? "",
      status: initial.status,
      notes: initial.notes ?? "",
    });
  }, [initial, reset]);

  const submit = handleSubmit(async (values) => {
    const imageInput = (document.getElementById("asset-image") as HTMLInputElement | null)
      ?.files?.[0] ?? null;
    await onSubmit(values, imageInput);
  });

  const addCategory = async () => {
    if (!newCategory.name.trim() || !newCategory.code.trim()) return;
    setLookupBusy(true);
    setLookupError(null);
    try {
      const created = await onCreateCategory({
        name: newCategory.name.trim(),
        code: newCategory.code.trim().toUpperCase(),
      });
      setValue("category", created.id, { shouldValidate: true });
      setNewCategory({ name: "", code: "" });
      setShowNewCategory(false);
    } catch {
      setLookupError("Could not create category (duplicate name/code?).");
    } finally {
      setLookupBusy(false);
    }
  };

  const addVendor = async () => {
    if (!newVendorName.trim()) return;
    setLookupBusy(true);
    setLookupError(null);
    try {
      const created = await onCreateVendor({ name: newVendorName.trim() });
      setValue("vendor", created.id, { shouldValidate: true });
      setNewVendorName("");
      setShowNewVendor(false);
    } catch {
      setLookupError("Could not create vendor (duplicate name?).");
    } finally {
      setLookupBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-6">
      {lookupError && (
        <p className="text-sm text-destructive" role="alert">
          {lookupError}
        </p>
      )}
      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Asset tag" error={errors.asset_tag?.message}>
          <Input {...register("asset_tag")} placeholder="AST-001" />
        </Field>
        <Field label="Name" error={errors.name?.message}>
          <Input {...register("name")} placeholder="MacBook Pro 14" />
        </Field>
        <div className="space-y-2 md:col-span-2">
          <Field label="Category" error={errors.category?.message}>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              {...register("category")}
            >
              <option value="">Select category</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </Field>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setShowNewCategory((v) => !v)}
          >
            {showNewCategory ? "Cancel new category" : "+ Add category"}
          </Button>
          {showNewCategory && (
            <div className="grid gap-2 rounded-md border bg-muted/20 p-3 sm:grid-cols-3">
              <Input
                placeholder="Name (Laptop)"
                value={newCategory.name}
                onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
              />
              <Input
                placeholder="Code (LAPTOP)"
                value={newCategory.code}
                onChange={(e) => setNewCategory({ ...newCategory, code: e.target.value })}
              />
              <Button type="button" disabled={lookupBusy} onClick={() => void addCategory()}>
                Save category
              </Button>
            </div>
          )}
        </div>
        <Field label="Status" error={errors.status?.message}>
          <select
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
            {...register("status")}
          >
            {ASSET_STATUSES.map((status: AssetStatus) => (
              <option key={status} value={status}>
                {status.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Brand" error={errors.brand?.message}>
          <Input {...register("brand")} />
        </Field>
        <Field label="Model" error={errors.model?.message}>
          <Input {...register("model")} />
        </Field>
        <Field label="Serial number" error={errors.serial_number?.message}>
          <Input {...register("serial_number")} />
        </Field>
        <div className="space-y-2">
          <Field label="Vendor" error={errors.vendor?.message as string | undefined}>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              {...register("vendor")}
            >
              <option value="">No vendor</option>
              {vendors.map((vendor) => (
                <option key={vendor.id} value={vendor.id}>
                  {vendor.name}
                </option>
              ))}
            </select>
          </Field>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setShowNewVendor((v) => !v)}
          >
            {showNewVendor ? "Cancel new vendor" : "+ Add vendor"}
          </Button>
          {showNewVendor && (
            <div className="flex gap-2">
              <Input
                placeholder="Vendor name"
                value={newVendorName}
                onChange={(e) => setNewVendorName(e.target.value)}
              />
              <Button type="button" disabled={lookupBusy} onClick={() => void addVendor()}>
                Save
              </Button>
            </div>
          )}
        </div>
        <Field label="Purchase date" error={errors.purchase_date?.message}>
          <Input type="date" {...register("purchase_date")} />
        </Field>
        <Field label="Warranty expiry" error={errors.warranty_expiry?.message}>
          <Input type="date" {...register("warranty_expiry")} />
        </Field>
        <Field label="Purchase cost" error={errors.purchase_cost?.message}>
          <Input type="number" step="0.01" min="0" {...register("purchase_cost")} />
        </Field>
        <Field label="Image" error={undefined}>
          <Input id="asset-image" type="file" accept="image/*" />
          {initial?.image_url && (
            <p className="mt-1 text-xs text-muted-foreground">
              Current image attached. Upload a new file to replace it.
            </p>
          )}
        </Field>
      </div>
      <Field label="Notes" error={errors.notes?.message}>
        <Textarea rows={4} {...register("notes")} />
      </Field>
      <div className="flex gap-3">
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving…" : initial ? "Update asset" : "Create asset"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel} disabled={submitting}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
