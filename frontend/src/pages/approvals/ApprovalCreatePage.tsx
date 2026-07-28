import { zodResolver } from "@hookform/resolvers/zod";
import { isAxiosError } from "axios";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/hooks/useAuth";
import { approvalService } from "@/services/approval.service";
import { assetService } from "@/services/asset.service";
import type { AssetCategory, AssetListItem } from "@/types/assets";
import { REQUEST_PRIORITIES } from "@/types/approvals";

const schema = z
  .object({
    category: z.union([z.coerce.number().int().positive(), z.literal("")]),
    asset: z.union([z.coerce.number().int().positive(), z.literal("")]),
    justification: z.string().min(10, "Explain why you need this (min 10 chars)"),
    priority: z.enum(["LOW", "MEDIUM", "HIGH", "URGENT"]),
  })
  .refine((v) => Boolean(v.category) || Boolean(v.asset), {
    message: "Select a category and/or a specific asset.",
    path: ["category"],
  });

type FormValues = z.infer<typeof schema>;

export function ApprovalCreatePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [categories, setCategories] = useState<AssetCategory[]>([]);
  const [assets, setAssets] = useState<AssetListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      category: "",
      asset: "",
      justification: "",
      priority: "MEDIUM",
    },
  });

  useEffect(() => {
    if (!user?.employee_profile) {
      navigate("/approvals", { replace: true });
    }
  }, [user, navigate]);

  useEffect(() => {
    const load = async () => {
      const [cats, available] = await Promise.all([
        assetService.listCategories(),
        assetService.list({ status: "AVAILABLE", ordering: "asset_tag", page: 1 }),
      ]);
      setCategories(cats.results);
      setAssets(available.results);
    };
    void load().catch(() => setError("Failed to load form options."));
  }, []);

  const onSubmit = handleSubmit(async (values) => {
    setSubmitting(true);
    setError(null);
    try {
      const created = await approvalService.create({
        category: values.category === "" ? null : Number(values.category),
        asset: values.asset === "" ? null : Number(values.asset),
        justification: values.justification,
        priority: values.priority,
      });
      navigate(`/approvals/${created.id}`);
    } catch (err) {
      if (isAxiosError(err) && err.response?.data) {
        setError(JSON.stringify(err.response.data));
      } else {
        setError("Could not submit request.");
      }
    } finally {
      setSubmitting(false);
    }
  });

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <Link to="/approvals" className="text-sm text-muted-foreground hover:text-foreground">
          ← Back to approvals
        </Link>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">New asset request</h1>
        <p className="text-sm text-muted-foreground">
          Your department manager will review this request. Email placeholders are logged on the
          server.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Request details</CardTitle>
          <CardDescription>
            Signed in as {user?.employee_profile?.employee_code} ·{" "}
            {user?.employee_profile?.department_name}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            {error && <p className="text-sm text-destructive">{error}</p>}
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <select
                id="category"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                {...register("category")}
              >
                <option value="">Any / not specified</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
              {errors.category && (
                <p className="text-xs text-destructive">{errors.category.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="asset">Specific available asset (optional)</Label>
              <select
                id="asset"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                {...register("asset")}
              >
                <option value="">No specific asset</option>
                {assets.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.asset_tag} — {a.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <select
                id="priority"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                {...register("priority")}
              >
                {REQUEST_PRIORITIES.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="justification">Justification</Label>
              <Textarea id="justification" rows={5} {...register("justification")} />
              {errors.justification && (
                <p className="text-xs text-destructive">{errors.justification.message}</p>
              )}
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={submitting}>
                {submitting ? "Submitting…" : "Submit request"}
              </Button>
              <Button type="button" variant="outline" onClick={() => navigate("/approvals")}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
