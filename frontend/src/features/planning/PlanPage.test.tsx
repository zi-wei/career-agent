import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { expect, it, vi } from "vitest";

import { planningApi, practiceApi } from "../../api/client";
import { BackgroundTaskProvider } from "../../app/BackgroundTasks";
import { PlanPage } from "./PlanPage";

vi.mock("../../api/client", () => ({
  ApiError: class ApiError extends Error {},
  planningApi: { latestPlan: vi.fn(), createPlan: vi.fn() },
  practiceApi: { fromPlan: vi.fn() },
}));

it("regenerates an existing plan as a new revision", async () => {
  const plan = {
    id: "plan-1", job_version_id: "version-1", revision: 1, status: "active",
    timezone: "Asia/Shanghai", starts_on: "2026-08-31", days: Array.from({ length: 14 }, (_, index) => ({
      day_number: index + 1, date: `2026-09-${String(index + 1).padStart(2, "0")}`,
      tasks: [{ id: `task-${index}`, kind: "learning", title: "Docker知识训练", objective: "学习Docker", completion_condition: "完成记录", requirement_id: "req-1", status: "pending" }],
    })),
  };
  vi.mocked(planningApi.latestPlan).mockResolvedValue(plan);
  vi.mocked(planningApi.createPlan).mockResolvedValue({ ...plan, id: "plan-2", revision: 2 });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><BackgroundTaskProvider><MemoryRouter initialEntries={["/jobs/job-1/plan"]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><Routes><Route path="/jobs/:jobId/plan" element={<PlanPage />} /></Routes></MemoryRouter></BackgroundTaskProvider></QueryClientProvider>);

  await userEvent.click(await screen.findByRole("button", { name: "重新生成计划" }));

  expect(planningApi.createPlan).toHaveBeenCalledWith("job-1");
  expect(await screen.findByText("版本 2")).toBeVisible();
});
