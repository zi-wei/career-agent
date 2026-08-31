import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";

import { evidenceApi, practiceApi } from "../../api/client";
import { BackgroundTaskProvider } from "../../app/BackgroundTasks";
import { PracticePage } from "./PracticePage";

vi.mock("../../api/client", () => ({
  practiceApi: {
    list: vi.fn(), start: vi.fn(), submit: vi.fn(), evaluate: vi.fn(), fromPlan: vi.fn(), remove: vi.fn(),
  },
  evidenceApi: { list: vi.fn() },
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

function practiceTask() {
  return {
    id: "task-1", plan_id: "plan-1", plan_task_id: "pt-1", job_version_id: "v1",
    requirement_ids: ["r1"], kind: "learning", title: "Docker知识训练",
    objective: "完成排查", instructions: "记录步骤", acceptance_criteria: ["完成记录"],
    deliverables: ["排查记录"], guidance: {
      explanation: "Docker通过隔离运行环境交付服务.",
      key_concepts: [{ name: "容器网络", explanation: "理解端口映射和网络命名空间." }],
      scenario_question: "容器无法访问时如何排查?",
      answer_framework: ["确认现象", "检查端口和日志"],
      self_checks: ["能否解释端口映射?", "能否说明验证依据?"],
    }, status: "in_progress", updated_at: "2026-08-31T00:00:00Z",
  };
}

it("submits a practice result and shows the created evidence", async () => {
  vi.mocked(practiceApi.list).mockResolvedValue({
    items: [practiceTask()],
  });
  vi.mocked(practiceApi.submit).mockResolvedValue({
    id: "submission-1", task_id: "task-1", content: "排查完成", artifact_refs: [],
    report_summary: "检查端口", status: "submitted", created_at: "2026-08-31T00:00:00Z",
  });
  vi.mocked(practiceApi.evaluate).mockResolvedValue({
    id: "eval-1", submission_id: "submission-1", advisory: true, summary: "已评价",
    strengths: [], improvements: [], created_at: "2026-08-31T00:00:00Z",
  });
  vi.mocked(evidenceApi.list).mockResolvedValue({ items: [] });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><BackgroundTaskProvider><MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><PracticePage /></MemoryRouter></BackgroundTaskProvider></QueryClientProvider>);
  const user = userEvent.setup();

  expect(await screen.findByText("Docker通过隔离运行环境交付服务.")).toBeVisible();
  expect(screen.getByText("容器网络")).toBeVisible();
  expect(screen.getByText("容器无法访问时如何排查?")).toBeVisible();
  await user.type(await screen.findByLabelText("提交内容"), "排查完成");
  await user.click(screen.getByRole("button", { name: "提交并评价" }));

  expect(await screen.findByText("已生成证据")).toBeVisible();
});

it("deletes a practice task after confirmation", async () => {
  vi.mocked(practiceApi.list).mockResolvedValue({ items: [practiceTask()] });
  vi.mocked(practiceApi.remove).mockResolvedValue(undefined);
  vi.spyOn(window, "confirm").mockReturnValue(true);
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><BackgroundTaskProvider><MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><PracticePage /></MemoryRouter></BackgroundTaskProvider></QueryClientProvider>);
  const user = userEvent.setup();

  await user.click(await screen.findByRole("button", { name: "删除实训任务" }));

  await waitFor(() => expect(practiceApi.remove).toHaveBeenCalledWith("task-1"));
  expect(window.confirm).toHaveBeenCalled();
});
