import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { RequireRole } from "@/components/RequireRole";
import { AuthLayout } from "@/layouts/AuthLayout";
import { MainLayout } from "@/layouts/MainLayout";
import { ApprovalCreatePage } from "@/pages/approvals/ApprovalCreatePage";
import { ApprovalDetailPage } from "@/pages/approvals/ApprovalDetailPage";
import { ApprovalListPage } from "@/pages/approvals/ApprovalListPage";
import { YourRequestsPage } from "@/pages/approvals/YourRequestsPage";
import { AssetDetailPage } from "@/pages/assets/AssetDetailPage";
import { AssetFormPage } from "@/pages/assets/AssetFormPage";
import { AssetListPage } from "@/pages/assets/AssetListPage";
import { MasterDataPage } from "@/pages/assets/MasterDataPage";
import { QrScanPage } from "@/pages/assets/QrScanPage";
import { AuditLogPage } from "@/pages/audit/AuditLogPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { EmployeesPage } from "@/pages/employees/EmployeesPage";
import { HomePage } from "@/pages/HomePage";
import { LoginPage } from "@/pages/LoginPage";
import { MaintenancePage } from "@/pages/maintenance/MaintenancePage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { NotificationsPage } from "@/pages/notifications/NotificationsPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { ReportsPage } from "@/pages/reports/ReportsPage";
import { UsersPage } from "@/pages/users/UsersPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />

      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/assets" element={<AssetListPage />} />
          <Route path="/assets/new" element={<AssetFormPage />} />
          <Route path="/assets/:id" element={<AssetDetailPage />} />
          <Route path="/assets/:id/edit" element={<AssetFormPage />} />
          <Route path="/maintenance" element={<MaintenancePage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/profile" element={<ProfilePage />} />

          <Route element={<RequireRole roles={["EMPLOYEE"]} />}>
            <Route path="/your-requests" element={<YourRequestsPage />} />
          </Route>

          <Route
            element={
              <RequireRole roles={["ADMIN", "ASSET_MANAGER", "IT_TEAM", "MANAGER"]} />
            }
          >
            <Route path="/approvals" element={<ApprovalListPage />} />
            <Route path="/approvals/:id" element={<ApprovalDetailPage />} />
            <Route path="/employees" element={<EmployeesPage />} />
            <Route path="/reports" element={<ReportsPage />} />
          </Route>

          {/* Keep /approvals/new for managers who request? Employees use Your Requests */}
          <Route element={<RequireRole roles={["EMPLOYEE", "MANAGER"]} />}>
            <Route path="/approvals/new" element={<ApprovalCreatePage />} />
          </Route>

          <Route element={<RequireRole roles={["ADMIN"]} />}>
            <Route path="/users" element={<UsersPage />} />
          </Route>

          <Route element={<RequireRole roles={["ADMIN", "ASSET_MANAGER", "IT_TEAM"]} />}>
            <Route path="/assets/scan" element={<QrScanPage />} />
            <Route path="/master-data" element={<MasterDataPage />} />
            <Route path="/audit" element={<AuditLogPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="/home" element={<Navigate to="/" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
