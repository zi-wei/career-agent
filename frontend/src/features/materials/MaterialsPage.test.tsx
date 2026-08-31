import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";

import { ApiError, materialsApi } from "../../api/client";
import type { MaterialBundle } from "../../api/client";
import { BackgroundTaskProvider } from "../../app/BackgroundTasks";
import { MaterialsPage } from "./MaterialsPage";

vi.mock("../../api/client", async (importOriginal) => {
  const original = await importOriginal<typeof import("../../api/client")>();
  return {
    ...original,
    materialsApi: {
      latest: vi.fn(),
      generate: vi.fn(),
      revise: vi.fn(),
      exportUrl: vi.fn(() => "/api/materials/resumes/resume-1/export?format=markdown"),
    },
  };
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <BackgroundTaskProvider>
        <MemoryRouter
          initialEntries={["/jobs/job-1/materials"]}
          future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
        >
          <Routes>
            <Route path="/jobs/:jobId/materials" element={<MaterialsPage />} />
          </Routes>
        </MemoryRouter>
      </BackgroundTaskProvider>
    </QueryClientProvider>,
  );
}

function materialBundle(revision = 1): MaterialBundle {
  return {
    job_id: "job-1",
    resume: {
      id: `resume-${revision}`,
      root_id: "resume-1",
      previous_revision_id: revision > 1 ? `resume-${revision - 1}` : null,
      job_version_id: "version-1",
      revision,
      status: "draft",
      target_title: "Linux 运维实习生",
      summary: "目标岗位: Linux 运维实习生",
      sections: [{
        kind: "project",
        title: "项目经历",
        bullets: [{ text: "使用 Docker 部署 Nginx 服务.", source_refs: ["profile_fact:fact-1"] }],
      }],
    },
    interview_pack: {
      id: `pack-${revision}`,
      job_version_id: "version-1",
      revision,
      status: "draft",
      title: "Linux 运维实习生面试题",
      questions: [],
    },
  };
}

it("generates initial materials before any strengthening workflow", async () => {
  vi.mocked(materialsApi.latest).mockRejectedValue(new ApiError(404, "materials_not_found"));
  vi.mocked(materialsApi.generate).mockResolvedValue(materialBundle());
  const user = userEvent.setup();
  renderPage();

  await user.click(await screen.findByRole("button", { name: "生成求职材料" }));

  expect(await screen.findByRole("textbox", { name: "简历简介" })).toHaveTextContent("目标岗位: Linux 运维实习生");
  expect(materialsApi.generate).toHaveBeenCalledWith("job-1");
});

it("shows generation progress while the model request is pending", async () => {
  vi.mocked(materialsApi.latest).mockRejectedValue(new ApiError(404, "materials_not_found"));
  vi.mocked(materialsApi.generate).mockImplementation(() => new Promise(() => undefined));
  const user = userEvent.setup();
  renderPage();

  await user.click(await screen.findByRole("button", { name: "生成求职材料" }));

  expect(screen.getByRole("progressbar", { name: "材料生成进度" })).toBeVisible();
  expect(screen.getByText(/正在分析JD并生成简历与面试题/)).toBeVisible();
});

it("shows a useful error and retry action when generation fails", async () => {
  vi.mocked(materialsApi.latest).mockRejectedValue(new ApiError(404, "materials_not_found"));
  vi.mocked(materialsApi.generate).mockRejectedValue(new ApiError(503, "invalid_model_output"));
  const user = userEvent.setup();
  renderPage();

  await user.click(await screen.findByRole("button", { name: "生成求职材料" }));

  expect(await screen.findByText("模型返回的材料格式不完整, 请重新生成.")).toBeVisible();
  expect(screen.getByRole("button", { name: "重新生成" })).toBeEnabled();
});

it("renders an editable A4 resume with avatar and export controls", async () => {
  vi.mocked(materialsApi.latest).mockResolvedValue(materialBundle());
  const print = vi.spyOn(window, "print").mockImplementation(() => undefined);
  renderPage();

  expect(await screen.findByLabelText("A4简历预览")).toBeVisible();
  expect(screen.getByRole("textbox", { name: "姓名" })).toHaveAttribute("contenteditable", "true");
  expect(screen.getByRole("textbox", { name: "简历简介" })).toHaveTextContent("目标岗位: Linux 运维实习生");
  expect(screen.getByRole("textbox", { name: "项目经历第1条" })).toHaveTextContent("使用 Docker 部署 Nginx 服务.");
  expect(screen.getByLabelText("上传头像")).toHaveAttribute("accept", "image/png,image/jpeg,image/webp");
  expect(screen.getByRole("button", { name: "下载HTML" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "重新生成材料" })).toBeEnabled();

  await userEvent.click(screen.getByRole("button", { name: "导出PDF" }));
  expect(print).toHaveBeenCalledOnce();
});

it("regenerates existing materials as a new version", async () => {
  vi.mocked(materialsApi.latest).mockResolvedValue(materialBundle());
  vi.mocked(materialsApi.generate).mockResolvedValue(materialBundle(2));
  const user = userEvent.setup();
  renderPage();

  await user.click(await screen.findByRole("button", { name: "重新生成材料" }));

  expect(materialsApi.generate).toHaveBeenCalledWith("job-1");
  expect(await screen.findByText("版本 2")).toBeVisible();
});
