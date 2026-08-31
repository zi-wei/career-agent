import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { expect, it, vi } from "vitest";

import { applicationsApi } from "../../api/client";
import { BackgroundTaskProvider } from "../../app/BackgroundTasks";
import { ApplicationsPage } from "./ApplicationsPage";

vi.mock("../../api/client", () => ({
  applicationsApi: { list: vi.fn(), updateStatus: vi.fn(), addFeedback: vi.fn(), advice: vi.fn() },
}));

it("updates an application status from the board", async () => {
  vi.mocked(applicationsApi.list).mockResolvedValue({
    items: [{ id: "app-1", job_id: "job-1", job_version_id: "v1", resume_id: "resume-1",
      status: "lead", channel: "BOSS直聘", notes: "", history: [],
      created_at: "2026-08-31T00:00:00Z", updated_at: "2026-08-31T00:00:00Z" }],
  });
  vi.mocked(applicationsApi.updateStatus).mockResolvedValue({
    id: "app-1", job_id: "job-1", job_version_id: "v1", resume_id: "resume-1",
    status: "applied", channel: "BOSS直聘", notes: "", history: [],
    created_at: "2026-08-31T00:00:00Z", updated_at: "2026-08-31T00:00:00Z",
  });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><BackgroundTaskProvider><MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><ApplicationsPage /></MemoryRouter></BackgroundTaskProvider></QueryClientProvider>);
  const user = userEvent.setup();

  await user.selectOptions(await screen.findByLabelText("更新投递状态"), "applied");
  await user.click(screen.getByRole("button", { name: "保存状态" }));

  expect(applicationsApi.updateStatus).toHaveBeenCalledWith("app-1", "applied", "");
});
