import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { collectorApi, jobsApi } from "../../api/client";
import { JobsPage } from "./JobsPage";

vi.mock("../../api/client", () => ({
  jobsApi: {
    list: vi.fn(),
    clear: vi.fn(),
    updateSaved: vi.fn(),
    remove: vi.fn(),
    batchAction: vi.fn(),
    paste: vi.fn(),
    importJson: vi.fn(),
  },
  collectorApi: {
    status: vi.fn(),
    createTask: vi.fn(),
    pause: vi.fn(),
    resume: vi.fn(),
    login: vi.fn(),
    cities: vi.fn(),
  },
}));

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <JobsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("JobsPage", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(jobsApi.list).mockResolvedValue({ items: [] });
    vi.mocked(collectorApi.status).mockResolvedValue({
      companion: { status: "running" },
      worker: { status: "running", pid: 123 },
      login: { status: "unknown", pid: null },
      task: null,
    });
    vi.mocked(collectorApi.cities).mockResolvedValue({
      items: [
        { name: "全国", code: "100010000", pinyin: "" },
        { name: "上海", code: "101020100", pinyin: "shanghai" },
        { name: "临沂", code: "101120900", pinyin: "linyi" },
      ],
    });
  });

  it("imports a pasted JD and updates the list", async () => {
    vi.mocked(jobsApi.paste).mockResolvedValue({
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
        description: "负责 Linux 系统维护",
        detail_status: "complete",
        snapshot: {},
      },
      versions: [],
      requirements: [],
    });
    const user = userEvent.setup();
    renderPage();

    await screen.findByText("暂无待筛选职位");
    await user.click(screen.getByRole("button", { name: "导入职位" }));
    await user.type(screen.getByLabelText("职位名称"), "Linux 运维实习生");
    await user.type(screen.getByLabelText("公司"), "示例科技");
    await user.type(screen.getByLabelText("JD 原文"), "负责 Linux 系统维护");
    await user.click(screen.getByRole("button", { name: "确认导入" }));

    expect(await screen.findByText("Linux 运维实习生")).toBeInTheDocument();
    expect(jobsApi.paste).toHaveBeenCalledOnce();
  });

  it("replaces an imported job when the API returns a newer version", async () => {
    const importedJob = {
      id: "job-1",
      source: "boss",
      source_job_id: "boss-linux-001",
      title: "Linux 运维实习生",
      company: "示例科技",
      city: "上海",
      is_saved: false,
      current_version: {
        id: "version-2",
        ordinal: 2,
        content_hash: "hash-2",
        version_hash: "version-hash-2",
        description: "负责 Linux 系统维护和 Docker 部署",
        detail_status: "complete",
        snapshot: {},
      },
      versions: [],
      requirements: [],
    };
    vi.mocked(jobsApi.importJson).mockResolvedValue(importedJob);
    const user = userEvent.setup();
    renderPage();

    await screen.findByText("暂无待筛选职位");
    for (let attempt = 0; attempt < 2; attempt += 1) {
      await user.click(screen.getByRole("button", { name: "导入职位" }));
      await user.click(screen.getByRole("button", { name: "导入 JSON" }));
      fireEvent.change(screen.getByLabelText("JobPosting v1 JSON"), {
        target: { value: "{}" },
      });
      await user.click(screen.getByRole("button", { name: "确认导入" }));
      await screen.findByText("Linux 运维实习生");
    }

    expect(screen.getAllByText("Linux 运维实习生")).toHaveLength(1);
    expect(screen.getByText("v2")).toBeInTheDocument();
  });

  it("clears every job after explicit confirmation", async () => {
    const job = {
      id: "job-1",
      source: "boss",
      source_job_id: "boss-1",
      title: "Linux 运维实习生",
      company: "示例科技",
      city: "临沂",
      is_saved: false,
      current_version: {
        id: "version-1",
        ordinal: 1,
        content_hash: "hash",
        version_hash: "version-hash",
        description: "负责 Linux 系统维护",
        detail_status: "complete",
        snapshot: {},
      },
      versions: [],
      requirements: [],
    };
    vi.mocked(jobsApi.list).mockResolvedValue({ items: [job] });
    vi.mocked(jobsApi.clear).mockResolvedValue({ deleted_count: 1 });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();
    renderPage();

    await screen.findByText("Linux 运维实习生");
    await user.click(screen.getByRole("button", { name: "清空职位" }));

    expect(window.confirm).toHaveBeenCalledWith(
      "确认清空全部职位? 关联的求职材料、计划和投递记录也会删除, 此操作不可撤销.",
    );
    expect(jobsApi.clear).toHaveBeenCalledOnce();
    expect(await screen.findByText("已清空 1 个职位.")).toBeVisible();
    expect(screen.getByText("暂无待筛选职位")).toBeVisible();
  });

  it("moves a collected job into saved jobs", async () => {
    const job = {
      id: "job-1", source: "boss", source_job_id: "boss-1", title: "Linux 运维实习生",
      company: "示例科技", city: "济南", is_saved: false,
      current_version: {
        id: "version-1", ordinal: 1, content_hash: "hash", version_hash: "version-hash",
        description: "负责 Linux 系统维护", detail_status: "complete", snapshot: {},
      },
      versions: [], requirements: [],
    };
    vi.mocked(jobsApi.list).mockResolvedValue({ items: [job] });
    vi.mocked(jobsApi.updateSaved).mockResolvedValue({ ...job, is_saved: true });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "收藏 Linux 运维实习生" }));
    await user.click(screen.getByRole("button", { name: "已收藏 1" }));

    expect(jobsApi.updateSaved).toHaveBeenCalledWith("job-1", true);
    expect(screen.getByText("Linux 运维实习生")).toBeVisible();
  });

  it("deletes one job after confirmation", async () => {
    const job = {
      id: "job-1", source: "boss", source_job_id: "boss-1", title: "Linux 运维实习生",
      company: "示例科技", city: "济南", is_saved: false,
      current_version: {
        id: "version-1", ordinal: 1, content_hash: "hash", version_hash: "version-hash",
        description: "负责 Linux 系统维护", detail_status: "complete", snapshot: {},
      },
      versions: [], requirements: [],
    };
    vi.mocked(jobsApi.list).mockResolvedValue({ items: [job] });
    vi.mocked(jobsApi.remove).mockResolvedValue(undefined);
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "删除 Linux 运维实习生" }));

    expect(jobsApi.remove).toHaveBeenCalledWith("job-1");
    expect(screen.getByText("暂无待筛选职位")).toBeVisible();
  });

  it("deletes selected jobs in one batch", async () => {
    const jobs = [1, 2].map((index) => ({
      id: `job-${index}`, source: "boss", source_job_id: `boss-${index}`,
      title: `运维实习生 ${index}`, company: `示例科技 ${index}`, city: "济南", is_saved: false,
      current_version: {
        id: `version-${index}`, ordinal: 1, content_hash: `hash-${index}`,
        version_hash: `version-hash-${index}`, description: "负责 Linux 系统维护",
        detail_status: "complete", snapshot: {},
      },
      versions: [], requirements: [],
    }));
    vi.mocked(jobsApi.list).mockResolvedValue({ items: jobs });
    vi.mocked(jobsApi.batchAction).mockResolvedValue({ affected_count: 2 });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("checkbox", { name: "选择 运维实习生 1" }));
    await user.click(screen.getByRole("checkbox", { name: "选择 运维实习生 2" }));
    await user.click(screen.getByRole("button", { name: "批量删除" }));

    expect(jobsApi.batchAction).toHaveBeenCalledWith(["job-1", "job-2"], "delete");
    expect(screen.getByText("暂无待筛选职位")).toBeVisible();
  });

  it("creates a background BOSS collection task", async () => {
    vi.mocked(collectorApi.createTask).mockResolvedValue({
      status: "queued",
      task: {
        id: "task-1",
        source: "boss",
        keyword: "运维实习生",
        city: "上海",
        requested_limit: 20,
        status: "queued",
        captured_count: 0,
        version_count: 0,
        pending_sync_count: 0,
        reason_code: null,
        resume_state: null,
      },
    });
    const user = userEvent.setup();
    renderPage();

    await screen.findByText("采集伴侣已连接");
    await user.click(screen.getByRole("button", { name: "采集职位" }));
    await user.clear(screen.getByLabelText("搜索关键词"));
    await user.type(screen.getByLabelText("搜索关键词"), "运维实习生");
    await user.clear(screen.getByLabelText("城市"));
    await user.type(screen.getByLabelText("城市"), "临沂");
    await user.clear(screen.getByLabelText("采集数量"));
    await user.type(screen.getByLabelText("采集数量"), "20");
    await user.click(screen.getByRole("button", { name: "开始后台采集" }));

    expect(collectorApi.createTask).toHaveBeenCalledWith({
      source: "boss",
      keyword: "运维实习生",
      city: "临沂",
      limit: 20,
    });
    expect(await screen.findByText("任务已加入后台队列.")).toBeVisible();
  });

  it("shows the local companion startup command when offline", async () => {
    vi.mocked(collectorApi.status).mockRejectedValue(new TypeError("Failed to fetch"));

    renderPage();

    expect(await screen.findByText("本机采集伴侣未启动")).toBeVisible();
    expect(screen.getByText("career-collector start")).toBeVisible();
  });

  it("opens BOSS login and resumes a task waiting for login", async () => {
    vi.mocked(collectorApi.status).mockResolvedValue({
      companion: { status: "running" },
      worker: { status: "running", pid: 123 },
      login: { status: "unknown", pid: null },
      task: {
        id: "task-1",
        source: "boss",
        keyword: "运维实习生",
        city: "上海",
        requested_limit: 20,
        status: "needs_login",
        captured_count: 0,
        version_count: 0,
        pending_sync_count: 0,
        reason_code: "login_required",
        resume_state: "checking_session",
      },
    });
    vi.mocked(collectorApi.login).mockResolvedValue({ status: "opening", pid: 456 });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "登录BOSS" }));

    expect(collectorApi.login).toHaveBeenCalledOnce();
    expect(await screen.findByText("BOSS专用窗口已打开, 完成登录或验证后请保持窗口开启, 然后继续采集.")).toBeVisible();
  });

  it("explains BOSS risk control and offers a visible action", async () => {
    vi.mocked(collectorApi.status).mockResolvedValue({
      companion: { status: "running" },
      worker: { status: "running", pid: 123 },
      login: { status: "browser_open", pid: 4321 },
      task: {
        id: "task-1",
        source: "boss",
        keyword: "运维实习生",
        city: "全国",
        requested_limit: 20,
        status: "needs_user_action",
        captured_count: 0,
        version_count: 0,
        pending_sync_count: 0,
        reason_code: "risk_control",
        resume_state: "checking_session",
      },
    });
    renderPage();

    expect(await screen.findByText("BOSS返回访问环境异常, 请在专用窗口完成验证并保持窗口开启, 然后继续采集.")).toBeVisible();
    expect(screen.getByRole("button", { name: "打开BOSS处理" })).toBeVisible();
  });
});
