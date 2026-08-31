import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, materialsApi, jobsApi, practiceApi, workspaceApi } from "../../api/client";
import { DashboardPage } from "./DashboardPage";

vi.mock("../../api/client", async (importOriginal) => {
  const original = await importOriginal<typeof import("../../api/client")>();
  return {
    ...original,
    workspaceApi: { get: vi.fn() },
    jobsApi: { list: vi.fn() },
    materialsApi: { latest: vi.fn() },
    practiceApi: { list: vi.fn() },
  };
});

const job = (id: string, isSaved: boolean) => ({
  id,
  source: "boss",
  source_job_id: `boss-${id}`,
  title: "Linux运维实习生",
  company: "示例科技",
  city: "上海",
  is_saved: isSaved,
  current_version: {
    id: `version-${id}`,
    ordinal: 1,
    content_hash: "hash",
    version_hash: "version-hash",
    description: "负责Linux与Docker环境维护",
    detail_status: "complete",
    snapshot: {},
  },
  versions: [],
  requirements: [],
});

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.mocked(practiceApi.list).mockResolvedValue({ items: [] });
    vi.mocked(materialsApi.latest).mockRejectedValue(new ApiError(404, "materials_not_found"));
  });

  it("guides a new user to complete the profile first", async () => {
    vi.mocked(workspaceApi.get).mockResolvedValue({
      id: "workspace-user", target_role: "", cities: [], availability: "", raw_resume: "", facts: [],
    });
    vi.mocked(jobsApi.list).mockResolvedValue({ items: [job("unsaved", false)] });

    renderPage();

    expect(await screen.findByRole("heading", { name: "先完成求职档案" })).toBeVisible();
    expect(screen.getByRole("link", { name: /完善档案/ })).toHaveAttribute("href", "/profile");
    expect(screen.getByText("第1步 / 共4步")).toBeVisible();
  });

  it("counts only saved jobs as target jobs", async () => {
    vi.mocked(workspaceApi.get).mockResolvedValue({
      id: "workspace-user", target_role: "运维实习生", cities: ["上海"], availability: "随时", raw_resume: "", facts: [],
    });
    vi.mocked(jobsApi.list).mockResolvedValue({ items: [job("unsaved", false), job("saved", true)] });

    renderPage();

    expect(await screen.findByRole("heading", { name: "为收藏职位生成求职材料" })).toBeVisible();
    expect(screen.getByText("1个目标职位")).toBeVisible();
    expect(materialsApi.latest).toHaveBeenCalledWith("saved");
  });

  it("continues with learning and practice after materials exist", async () => {
    vi.mocked(workspaceApi.get).mockResolvedValue({
      id: "workspace-user", target_role: "运维实习生", cities: ["上海"], availability: "随时", raw_resume: "", facts: [],
    });
    vi.mocked(jobsApi.list).mockResolvedValue({ items: [job("saved", true)] });
    vi.mocked(materialsApi.latest).mockResolvedValue({
      job_id: "saved",
      resume: { id: "resume-1", root_id: "resume-1", previous_revision_id: null, job_version_id: "version-saved", revision: 1, status: "draft", target_title: "Linux运维实习生", summary: "", sections: [] },
      interview_pack: { id: "pack-1", job_version_id: "version-saved", revision: 1, status: "draft", title: "面试题", questions: [] },
    });
    vi.mocked(practiceApi.list).mockResolvedValue({ items: [{
      id: "task-1", plan_id: "plan-1", plan_task_id: "plan-task-1", job_version_id: "version-saved",
      requirement_ids: [], kind: "guided_project", title: "完成Docker服务故障排查实训",
      objective: "完成一次可复现的故障排查", instructions: "", acceptance_criteria: [], deliverables: [],
      guidance: { instructions: "完成实训", checklist: [] }, status: "in_progress", updated_at: "2026-08-31T00:00:00Z",
    }] });

    renderPage();

    expect(await screen.findByRole("heading", { name: "继续完成学习与实训" })).toBeVisible();
    expect(screen.getByText("第4步 / 共4步")).toBeVisible();
    expect(screen.getByRole("link", { name: /继续实训/ })).toHaveAttribute("href", "/practice");
  });
});
