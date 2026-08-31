import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { JobDetailPage } from "../features/jobs/JobDetailPage";
import { JobsPage } from "../features/jobs/JobsPage";
import { MaterialsPage } from "../features/materials/MaterialsPage";
import { PlanPage } from "../features/planning/PlanPage";
import { SelectionPage } from "../features/planning/SelectionPage";
import { ProfilePage } from "../features/profile/ProfilePage";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { PracticePage } from "../features/practice/PracticePage";
import { EvidencePage } from "../features/evidence/EvidencePage";
import { ApplicationsPage } from "../features/applications/ApplicationsPage";
import { SettingsPage } from "../features/settings/SettingsPage";
import { AppShell } from "./AppShell";
import { BackgroundTaskProvider } from "./BackgroundTasks";

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BackgroundTaskProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppShell />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/jobs/:jobId" element={<JobDetailPage />} />
            <Route path="/jobs/:jobId/materials" element={<MaterialsPage />} />
            <Route path="/jobs/:jobId/selection" element={<SelectionPage />} />
            <Route path="/jobs/:jobId/plan" element={<PlanPage />} />
            <Route path="/practice" element={<PracticePage />} />
            <Route path="/evidence" element={<EvidencePage />} />
            <Route path="/applications" element={<ApplicationsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </BackgroundTaskProvider>
    </QueryClientProvider>
  );
}
