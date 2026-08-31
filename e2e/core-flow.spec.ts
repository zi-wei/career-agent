import { expect, test, type Page } from "@playwright/test";

const pastedTitle = "验收 Linux 运维实习生";
const runId = Date.now().toString();
const importedTitle = `验收平台运维实习生 ${runId}`;
const company = "Career Agent 验收公司";
const importedSourceId = `career-agent-e2e-${runId}`;

function importedJob(description: string, version: number) {
  return {
    payload_schema_version: "1",
    job: {
      source: "manual_fixture",
      source_job_id: importedSourceId,
      title: importedTitle,
      company,
      salary_text: "150-200元/天",
      city: "上海",
      district: null,
      experience: "在校生",
      education: "本科",
      company_scale: null,
      company_stage: null,
      industry: "企业服务",
      recruiter_title: null,
      recruiter_active_status: null,
      skills: ["Linux", "Docker", "Nginx"],
      benefits: [],
      description,
      source_url: null,
      published_at: null,
      first_seen_at: null,
      last_seen_at: null,
      content_hash: `career-agent-e2e-content-v${version}`,
      version_hash: `career-agent-e2e-version-v${version}`,
      detail_status: "complete",
      detail_checked_at: null,
      availability_status: "available",
      availability_checked_at: null,
      missing_observation_count: 0,
      collection_task_id: "career-agent-e2e",
      field_confidence: { title: 1, company: 1 },
    },
  };
}

async function openImportDialog(page: Page) {
  await page.getByRole("button", { name: "导入职位" }).click();
  await expect(page.getByRole("dialog", { name: "导入职位" })).toBeVisible();
}

async function importJson(page: Page, payload: unknown) {
  await openImportDialog(page);
  await page.getByRole("button", { name: "导入 JSON" }).click();
  await page.getByLabel("JobPosting v1 JSON").fill(JSON.stringify(payload));
  await page.getByRole("button", { name: "确认导入" }).click();
  await expect(page.getByRole("dialog", { name: "导入职位" })).toBeHidden();
}

test.describe.serial("Career Agent stage 1", () => {
  test("completes the core workflow", async ({ page }) => {
    const profileResponse = page.waitForResponse("**/api/workspace/profile");
    await page.goto("/profile");
    await profileResponse;
    await page.getByLabel("目标岗位").fill("Linux 运维实习生");
    await page.getByLabel("目标城市").fill("上海, 杭州");
    await page.getByLabel("到岗条件").fill("每周 5 天, 可立即到岗");
    await page.getByLabel("原始简历").fill("掌握 Linux 基础, 完成过个人服务器部署.");
    await page.getByRole("button", { name: "添加经历" }).click();
    await page.getByLabel("经历标题").last().fill("个人服务部署项目");
    await page.getByLabel("经历内容").last().fill("在本地使用 Docker Compose 部署 Web 服务并配置 Nginx.");
    await page.getByRole("button", { name: "保存档案" }).click();
    await expect(page.getByText("档案已保存")).toBeVisible();

    await page.getByRole("link", { name: "目标职位" }).click();
    await openImportDialog(page);
    await page.getByLabel("职位名称").fill(pastedTitle);
    await page.getByLabel("公司").fill(company);
    await page.getByLabel("城市").fill("上海");
    await page.getByLabel("JD 原文").fill(
      "负责 Linux 服务器日常维护, 使用 Docker 部署服务, 配置 Nginx 反向代理, 编写 Shell 脚本并排查故障.",
    );
    await page.getByRole("button", { name: "确认导入" }).click();
    await expect(page.getByText(pastedTitle, { exact: true })).toBeVisible();

    const firstImportedDescription = "负责 Linux 主机维护, 使用 Docker 和 Nginx 发布服务.";
    await importJson(page, importedJob(firstImportedDescription, 1));
    await importJson(page, importedJob(firstImportedDescription, 1));
    await expect(page.getByText(importedTitle, { exact: true })).toHaveCount(1);
    const importedRow = page.locator(".selectable-job-row").filter({ hasText: importedTitle });
    await expect(importedRow.getByText("v1", { exact: true })).toBeVisible();

    await importJson(
      page,
      importedJob(`${firstImportedDescription} 需要编写 Shell 自动化脚本.`, 2),
    );
    await expect(page.getByText(importedTitle, { exact: true })).toHaveCount(1);
    await expect(importedRow.getByText("v2", { exact: true })).toBeVisible();

    await page.getByText(pastedTitle, { exact: true }).click();
    await page.getByRole("link", { name: "准备求职材料" }).click();
    const generateButton = page.getByRole("button", { name: "生成求职材料" });
    const summary = page.getByLabel("简介");
    await expect(generateButton.or(summary)).toBeVisible();
    if (await generateButton.isVisible()) await generateButton.click();
    await expect(summary).toBeVisible();
    await summary.fill("目标岗位: Linux 运维实习生. 具备个人服务部署项目经验.");
    await page.getByRole("button", { name: "保存为新版本" }).click();
    await expect(page.locator(".page-heading .eyebrow")).toContainText(/版本 \d+/);

    await page.getByRole("link", { name: "下一步: 选择加强项" }).click();
    const dockerRequirement = page.locator(".requirement-list article").filter({
      has: page.getByRole("heading", { name: "Docker", exact: true }),
    });
    const nginxRequirement = page.locator(".requirement-list article").filter({
      has: page.getByRole("heading", { name: "Nginx", exact: true }),
    });
    await dockerRequirement.getByRole("radio", { name: "希望加强" }).check();
    await nginxRequirement.getByRole("radio", { name: "希望加强" }).check();
    await page.getByRole("button", { name: "生成14天计划" }).click();

    await expect(page.getByRole("heading", { name: "14天滚动计划" })).toBeVisible();
    await expect(page.locator(".plan-day")).toHaveCount(14);
    await expect(page.getByText(/Docker/).first()).toBeVisible();
    await expect(page.getByText(/Nginx/).first()).toBeVisible();
  });

  test("persists the generated materials and plan after reload", async ({ page }) => {
    await page.goto("/jobs");
    await page.getByRole("button", { name: /已收藏/ }).click();
    await page.getByText(pastedTitle, { exact: true }).click();
    await page.getByRole("link", { name: "求职材料", exact: true }).click();
    await expect(page.locator(".page-heading .eyebrow")).toContainText(/版本 \d+/);
    await page.getByRole("link", { name: "14天计划" }).click();
    await expect(page.getByRole("heading", { name: "14天滚动计划" })).toBeVisible();
    await expect(page.locator(".plan-day")).toHaveCount(14);
  });
});
