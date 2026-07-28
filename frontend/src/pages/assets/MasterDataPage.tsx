import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { assetService } from "@/services/asset.service";
import type { AssetCategory, Vendor } from "@/types/assets";

export function MasterDataPage() {
  const [categories, setCategories] = useState<AssetCategory[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [catForm, setCatForm] = useState({ name: "", code: "", description: "" });
  const [vendorForm, setVendorForm] = useState({
    name: "",
    contact_person: "",
    email: "",
    phone: "",
  });

  const load = useCallback(async () => {
    setError(null);
    try {
      const [cats, vends] = await Promise.all([
        assetService.listCategories(),
        assetService.listVendors(),
      ]);
      setCategories(cats.results);
      setVendors(vends.results);
    } catch {
      setError("Failed to load categories and vendors.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const createCategory = async () => {
    if (!catForm.name.trim() || !catForm.code.trim()) return;
    try {
      await assetService.createCategory({
        name: catForm.name.trim(),
        code: catForm.code.trim().toUpperCase(),
        description: catForm.description.trim() || undefined,
      });
      setCatForm({ name: "", code: "", description: "" });
      await load();
    } catch {
      setError("Could not create category.");
    }
  };

  const createVendor = async () => {
    if (!vendorForm.name.trim()) return;
    try {
      await assetService.createVendor({
        name: vendorForm.name.trim(),
        contact_person: vendorForm.contact_person.trim() || undefined,
        email: vendorForm.email.trim() || undefined,
        phone: vendorForm.phone.trim() || undefined,
      });
      setVendorForm({ name: "", contact_person: "", email: "", phone: "" });
      await load();
    } catch {
      setError("Could not create vendor.");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Categories &amp; Vendors</h1>
        <p className="text-sm text-muted-foreground">
          Master data used when creating and filtering assets.
        </p>
      </div>
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Asset categories</CardTitle>
            <CardDescription>{categories.length} active categories</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <ul className="space-y-2 text-sm">
              {categories.map((c) => (
                <li key={c.id} className="border-b pb-2">
                  <span className="font-mono text-xs">{c.code}</span> · {c.name}
                  {c.description ? (
                    <div className="text-xs text-muted-foreground">{c.description}</div>
                  ) : null}
                </li>
              ))}
              {categories.length === 0 && (
                <li className="text-muted-foreground">No categories yet.</li>
              )}
            </ul>
            <div className="grid gap-2">
              <div className="grid gap-2 sm:grid-cols-2">
                <div className="space-y-1">
                  <Label htmlFor="cat-name">Name</Label>
                  <Input
                    id="cat-name"
                    value={catForm.name}
                    onChange={(e) => setCatForm({ ...catForm, name: e.target.value })}
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="cat-code">Code</Label>
                  <Input
                    id="cat-code"
                    value={catForm.code}
                    onChange={(e) => setCatForm({ ...catForm, code: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-1">
                <Label htmlFor="cat-desc">Description</Label>
                <Textarea
                  id="cat-desc"
                  rows={2}
                  value={catForm.description}
                  onChange={(e) => setCatForm({ ...catForm, description: e.target.value })}
                />
              </div>
              <Button onClick={() => void createCategory()}>Add category</Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Vendors</CardTitle>
            <CardDescription>{vendors.length} active vendors</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <ul className="space-y-2 text-sm">
              {vendors.map((v) => (
                <li key={v.id} className="border-b pb-2">
                  <div className="font-medium">{v.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {[v.contact_person, v.email, v.phone].filter(Boolean).join(" · ") ||
                      "No contact details"}
                  </div>
                </li>
              ))}
              {vendors.length === 0 && (
                <li className="text-muted-foreground">No vendors yet.</li>
              )}
            </ul>
            <div className="grid gap-2">
              <div className="space-y-1">
                <Label htmlFor="vendor-name">Name</Label>
                <Input
                  id="vendor-name"
                  value={vendorForm.name}
                  onChange={(e) => setVendorForm({ ...vendorForm, name: e.target.value })}
                />
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <div className="space-y-1">
                  <Label htmlFor="vendor-contact">Contact</Label>
                  <Input
                    id="vendor-contact"
                    value={vendorForm.contact_person}
                    onChange={(e) =>
                      setVendorForm({ ...vendorForm, contact_person: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="vendor-phone">Phone</Label>
                  <Input
                    id="vendor-phone"
                    value={vendorForm.phone}
                    onChange={(e) => setVendorForm({ ...vendorForm, phone: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-1">
                <Label htmlFor="vendor-email">Email</Label>
                <Input
                  id="vendor-email"
                  type="email"
                  value={vendorForm.email}
                  onChange={(e) => setVendorForm({ ...vendorForm, email: e.target.value })}
                />
              </div>
              <Button onClick={() => void createVendor()}>Add vendor</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
