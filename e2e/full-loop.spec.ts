import { expect, test } from "@playwright/test";

const title = "闭环验收 Linux 运维实习生";

test.describe.serial("Career Agent full loop", () => {
  test("completes job to feedback loop", async ({ request, page }) => {
    await request.put("/api/workspace/profile", { data: {
      target_role: "Linux运维实习生", cities: ["上海"], availability: "每周5天",
      raw_resume: "完成个人服务器项目", facts: [{
        kind: "project", title: "个人服务器", content: "使用Docker部署Nginx并记录测试结果.",
      }],
    }});
    const jobResponse = await request.post("/api/jobs/paste", { data: {
      title, company: "闭环验收公司", city: "上海",
      description: "负责Linux系统维护, 使用Docker和Nginx部署服务, 编写Shell脚本.",
    }});
    expect(jobResponse.ok()).toBeTruthy();
    const job = await jobResponse.json();
    const materialsResponse = await request.post(`/api/jobs/${job.id}/materials`);
    expect(materialsResponse.ok()).toBeTruthy();
    const materials = await materialsResponse.json();
    const detail = await (await request.get(`/api/jobs/${job.id}`)).json();
    const selected = detail.requirements.slice(0, 2);
    await request.put(`/api/jobs/${job.id}/selections`, { data: {
      selections: selected.map((item: { id: string }) => ({ requirement_id: item.id, state: "strengthen" })),
    }});
    const plan = await (await request.post(`/api/jobs/${job.id}/plans`)).json();
    const tasksResponse = await request.post(`/api/practice/tasks/from-plan/${plan.id}`);
    expect(tasksResponse.ok()).toBeTruthy();
    const tasks = (await tasksResponse.json()).items;
    const knowledgeTask = tasks.find((item: { kind: string }) => item.kind === "learning");
    const projectTask = tasks.find((item: { kind: string }) => item.kind === "guided_project");
    expect(knowledgeTask.guidance.explanation).toBeTruthy();
    expect(knowledgeTask.guidance.key_concepts.length).toBeGreaterThan(0);
    expect(knowledgeTask.guidance.scenario_question).toBeTruthy();
    expect(projectTask.guidance.business_context).toBeTruthy();
    expect(projectTask.guidance.milestones.length).toBeGreaterThan(0);
    const task = knowledgeTask;
    await request.post(`/api/practice/tasks/${task.id}/start`);
    const submission = await (await request.post(`/api/practice/tasks/${task.id}/submissions`, { data: {
      content: "完成故障现象、排查步骤、验证方法和复盘记录.",
      artifact_refs: ["https://example.com/career-agent-e2e"],
      report_summary: "端口映射和日志检查完成.",
    }})).json();
    const evaluation = await request.post(`/api/practice/submissions/${submission.id}/evaluate`);
    expect(evaluation.ok()).toBeTruthy();
    const evidence = await (await request.get("/api/evidence")).json();
    expect(evidence.items.some((item: { source_id: string }) => item.source_id === submission.id)).toBeTruthy();

    const application = await (await request.post("/api/applications", { data: {
      job_id: job.id, resume_id: materials.resume.id, channel: "BOSS直聘", notes: "闭环验收",
    }})).json();
    await request.post(`/api/applications/${application.id}/status`, { data: { status: "applied", note: "已投递" } });
    await request.post(`/api/applications/${application.id}/status`, { data: { status: "rejected", note: "岗位暂停" } });
    await request.post(`/api/applications/${application.id}/feedback`, { data: {
      stage: "screening", outcome: "rejected", question: "", recorded_reason: "岗位暂停招聘", notes: "HR通知",
    }});
    const advice = await request.post(`/api/applications/${application.id}/advice`);
    expect(advice.ok()).toBeTruthy();
    expect((await advice.json()).summary).not.toContain("能力不足");

    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "从真实职位开始." })).toBeVisible();
    await page.getByRole("link", { name: "学习与实训" }).click();
    await expect(page.getByRole("heading", { name: "学习与实训" })).toBeVisible();
    await page.locator(".task-row").filter({ hasText: knowledgeTask.title }).first().click();
    await expect(page.getByRole("heading", { name: "知识讲解" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "场景题" })).toBeVisible();
    await page.locator(".task-row").filter({ hasText: projectTask.title }).first().click();
    await expect(page.getByRole("heading", { name: "业务背景" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "项目阶段" })).toBeVisible();
    await page.getByRole("link", { name: "证据记录" }).click();
    await expect(page.getByText(task.title, { exact: true }).first()).toBeVisible();
    await page.getByRole("link", { name: "投递进展" }).click();
    await expect(page.getByRole("heading", { name: "投递看板" })).toBeVisible();
  });

  test("persists full loop records", async ({ request }) => {
    const jobs = await (await request.get("/api/jobs")).json();
    const applications = await (await request.get("/api/applications")).json();
    const evidence = await (await request.get("/api/evidence")).json();
    expect(jobs.items.some((item: { title: string }) => item.title === title)).toBeTruthy();
    expect(applications.items.length).toBeGreaterThan(0);
    expect(evidence.items.length).toBeGreaterThan(0);
  });
});
