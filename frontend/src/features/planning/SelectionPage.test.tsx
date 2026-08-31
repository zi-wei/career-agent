import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { expect, it, vi } from "vitest";

import { jobsApi, planningApi } from "../../api/client";
import { BackgroundTaskProvider } from "../../app/BackgroundTasks";
import { SelectionPage } from "./SelectionPage";

vi.mock("../../api/client", () => ({
  jobsApi: { get: vi.fn() },
  planningApi: { updateSelections: vi.fn() },
}));

it("starts unselected and enables planning only after explicit choice", async () => {
  vi.mocked(jobsApi.get).mockResolvedValue({
    id: "job-1",
    source: "manual",
    source_job_id: "manual-1",
    title: "Linux 运维实习生",
    company: "示例科技",
    city: "上海",
    is_saved: true,
    current_version: {
      id: "version-1",
      ordinal: 1,
      content_hash: "hash",
      version_hash: "version-hash",
      description: "使用 Docker 部署服务",
      detail_status: "complete",
      snapshot: {},
    },
    versions: [],
    requirements: [
      {
        id: "requirement-1",
        label: "Docker",
        category: "container",
        evidence_text: "使用 Docker 部署服务",
        selection: "unselected",
      },
    ],
  });
  vi.mocked(planningApi.updateSelections).mockResolvedValue({ items: [] });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const user = userEvent.setup();
  render(
    <QueryClientProvider client={queryClient}>
      <BackgroundTaskProvider>
        <MemoryRouter
          initialEntries={["/jobs/job-1/selection"]}
          future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
        >
          <Routes>
            <Route path="/jobs/:jobId/selection" element={<SelectionPage />} />
          </Routes>
        </MemoryRouter>
      </BackgroundTaskProvider>
    </QueryClientProvider>,
  );

  const planButton = await screen.findByRole("button", { name: "生成14天计划" });
  expect(planButton).toBeDisabled();
  await user.click(await screen.findByRole("radio", { name: "希望加强" }));
  expect(planButton).toBeEnabled();
});
