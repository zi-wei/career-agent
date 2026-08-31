import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { runtimeApi } from "../api/client";
import { AppShell } from "./AppShell";
import { BackgroundTaskProvider } from "./BackgroundTasks";

vi.mock("../api/client", () => ({
  runtimeApi: { get: vi.fn() },
}));

function renderShell(path = "/dashboard") {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <BackgroundTaskProvider>
        <MemoryRouter initialEntries={[path]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="*" element={<p>页面内容</p>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </BackgroundTaskProvider>
    </QueryClientProvider>,
  );
}

describe("AppShell", () => {
  afterEach(cleanup);
  beforeEach(() => {
    window.localStorage.clear();
    vi.mocked(runtimeApi.get).mockResolvedValue({
      provider: "demo",
      model: "career-local",
      model_configured: true,
      collector_sync_enabled: true,
    });
  });

  it("organizes the main navigation around the job-search flow", async () => {
    renderShell();

    expect(screen.getByText("求职流程")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "求职概览" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "目标职位" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "投递进展" })).toBeInTheDocument();
    expect(await screen.findByText("系统正常")).toBeInTheDocument();
  });

  it("shows job-specific navigation while viewing a job", () => {
    renderShell("/jobs/job-1/materials");

    expect(screen.getByText("当前职位")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "求职材料" })).toHaveAttribute("href", "/jobs/job-1/materials");
    expect(screen.getByRole("link", { name: "14天计划" })).toHaveAttribute("href", "/jobs/job-1/plan");
  });

  it("keeps the current job navigation after opening a top-level page", async () => {
    const user = userEvent.setup();
    renderShell("/jobs/job-1/materials");

    await user.click(screen.getByRole("link", { name: "求职概览" }));

    expect(screen.getByText("当前职位")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "求职材料" })).toHaveAttribute("href", "/jobs/job-1/materials");
  });
});
