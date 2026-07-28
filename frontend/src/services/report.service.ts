import { apiClient } from "@/services/api";
import { tokenStorage } from "@/utils/tokenStorage";

async function downloadAuthenticatedFile(path: string, filename: string): Promise<void> {
  const token = tokenStorage.getAccessToken();
  const response = await fetch(`/api${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    throw new Error(`Download failed (${response.status})`);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export type ExportReportKey =
  | "assets-by-department"
  | "assets-by-category"
  | "allocation-history"
  | "maintenance-history";

export const reportService = {
  async inventory() {
    const { data } = await apiClient.get("/reports/inventory/");
    return data as {
      total: number;
      by_status: Array<{ status: string; count: number }>;
      by_category: Array<{ category: string; status: string; count: number }>;
    };
  },
  async warranty(days = 90) {
    const { data } = await apiClient.get("/reports/warranty/", { params: { days } });
    return data as {
      days: number;
      count: number;
      results: Array<{
        id: number;
        asset_tag: string;
        name: string;
        category: string;
        status: string;
        warranty_expiry: string;
      }>;
    };
  },
  async allocations() {
    const { data } = await apiClient.get("/reports/allocations/");
    return data as {
      results: Array<{
        department: string;
        department_code: string;
        active_allocations: number;
      }>;
    };
  },
  async requests() {
    const { data } = await apiClient.get("/reports/requests/");
    return data as { total: number; results: Array<{ status: string; count: number }> };
  },
  async assetsByDepartment() {
    const { data } = await apiClient.get("/reports/assets-by-department/");
    return data as {
      summary: Array<{ department: string; department_code: string; asset_count: number }>;
      results: Array<Record<string, string>>;
    };
  },
  async assetsByCategory() {
    const { data } = await apiClient.get("/reports/assets-by-category/");
    return data as {
      summary: Array<{ category: string; category_code: string; asset_count: number }>;
      results: Array<Record<string, string>>;
    };
  },
  async allocationHistory() {
    const { data } = await apiClient.get("/reports/allocation-history/");
    return data as { results: Array<Record<string, string>> };
  },
  async maintenanceHistory() {
    const { data } = await apiClient.get("/reports/maintenance-history/");
    return data as { results: Array<Record<string, string>> };
  },
  inventoryCsvUrl(): string {
    return "/api/reports/inventory.csv";
  },
  async downloadExcel(report: ExportReportKey): Promise<void> {
    await downloadAuthenticatedFile(
      `/reports/export/${report}.xlsx`,
      `${report}.xlsx`
    );
  },
  async downloadPdf(report: ExportReportKey): Promise<void> {
    await downloadAuthenticatedFile(`/reports/export/${report}.pdf`, `${report}.pdf`);
  },
};
