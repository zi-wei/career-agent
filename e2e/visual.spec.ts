import { expect, test, type Page } from "@playwright/test";

const pastedTitle = "验收 Linux 运维实习生";

async function mockCollector(page: Page) {
  await page.route("http://127.0.0.1:8765/v1/**", async (route) => {
    const request = route.request();
    if (request.url().endsWith("/status")) {
      await route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          companion: { status: "running" },
          worker: { status: "running", pid: 12001 },
          login: { status: "session_saved", pid: null },
          task: null,
        }),
      });
      return;
    }
    if (request.url().endsWith("/cities")) {
      await route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            { name: "全国", code: "100010000", pinyin: "" },
            { name: "上海", code: "101020100", pinyin: "shanghai" },
            { name: "临沂", code: "101120900", pinyin: "linyi" },
          ],
        }),
      });
      return;
    }
    if (request.url().endsWith("/tasks") && request.method() === "POST") {
      await route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          status: "queued",
          task: {
            id: "e2e-task",
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
        }),
      });
      return;
    }
    await route.fulfill({ status: 404, contentType: "application/json", body: "{}" });
  });
}

async function expectNoHorizontalOverflow(page: Page) {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth + 1);
}

test("renders the desktop materials workspace", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/jobs");
  await page.getByRole("button", { name: /已收藏/ }).click();
  await page.getByText(pastedTitle, { exact: true }).click();
  await page.getByRole("link", { name: "求职材料", exact: true }).click();
  await expect(page.getByRole("heading", { name: "求职材料" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: testInfo.outputPath("desktop-materials.png"), fullPage: true });
});

test("renders the mobile plan without horizontal overflow", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/jobs");
  await page.getByRole("button", { name: /已收藏/ }).click();
  await page.getByText(pastedTitle, { exact: true }).click();
  await page.getByRole("link", { name: "14天计划", exact: true }).click();
  await expect(page.getByRole("heading", { name: "14天滚动计划" })).toBeVisible();
  await expect(page.locator(".plan-day")).toHaveCount(14);
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: testInfo.outputPath("mobile-plan.png"), fullPage: true });
});

test("renders the desktop dashboard without horizontal overflow", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "从真实职位开始." })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: testInfo.outputPath("desktop-dashboard.png"), fullPage: true });
});

test("renders the mobile dashboard without horizontal overflow", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "从真实职位开始." })).toBeVisible();
  await expect(page.getByText("完整流程", { exact: true })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: testInfo.outputPath("mobile-dashboard.png"), fullPage: true });
});

test("renders the desktop job list without horizontal overflow", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await mockCollector(page);
  await page.goto("/jobs");
  await expect(page.getByRole("heading", { name: "真实职位" })).toBeVisible();
  await expect(page.getByText("采集伴侣已连接")).toBeVisible();
  await expect(page.getByRole("button", { name: "采集职位" })).toBeEnabled();
  await page.getByRole("button", { name: /已收藏/ }).click();
  await expect(page.locator(".selectable-job-row").first()).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: testInfo.outputPath("desktop-jobs.png"), fullPage: true });
});

test("creates a BOSS collection task from the desktop dialog", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await mockCollector(page);
  await page.goto("/jobs");
  await page.getByRole("button", { name: "采集职位" }).click();
  await expect(page.getByRole("dialog", { name: "采集BOSS职位" })).toBeVisible();
  await expect(page.getByLabel("搜索关键词")).toHaveValue("运维实习生");
  await page.getByLabel("城市").fill("临沂");
  await expect(page.getByLabel("城市")).toHaveValue("临沂");
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: testInfo.outputPath("desktop-collector-dialog.png"), fullPage: true });
  await page.getByRole("button", { name: "开始后台采集" }).click();
  await expect(page.getByText("任务已加入后台队列.")).toBeVisible();
});

test("renders the mobile collector dialog without horizontal overflow", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockCollector(page);
  await page.goto("/jobs");
  await page.getByRole("button", { name: "采集职位" }).click();
  await expect(page.getByRole("dialog", { name: "采集BOSS职位" })).toBeVisible();
  await expect(page.getByLabel("城市")).toHaveValue("上海");
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: testInfo.outputPath("mobile-collector-dialog.png"), fullPage: true });
});

test("renders mobile practice without page overflow", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/practice");
  await expect(page.getByRole("heading", { name: "学习与实训" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: testInfo.outputPath("mobile-practice.png"), fullPage: true });
});

test("renders structured practice guidance on desktop", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/practice");
  await expect(page.getByRole("heading", { name: "学习与实训" })).toBeVisible();
  await expect(page.locator(".guidance-content").first()).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: testInfo.outputPath("desktop-practice.png"), fullPage: true });
});

test("renders editable model settings on desktop", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/settings");
  await expect(page.getByRole("heading", { name: "设置" })).toBeVisible();
  await expect(page.getByLabel("服务地址")).toBeVisible();
  await expect(page.getByLabel("API Key")).toHaveAttribute("type", "password");
  await expect(page.getByLabel("模型")).toBeVisible();
  await expect(page.getByRole("button", { name: "拉取模型" })).toBeVisible();
  await expect(page.getByRole("button", { name: "保存并测试" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: testInfo.outputPath("desktop-settings.png"), fullPage: true });
});

test("wraps model settings and collector commands on mobile", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/settings");
  await expect(page.getByRole("heading", { name: "设置" })).toBeVisible();
  await expect(page.getByLabel("服务地址")).toBeVisible();
  await expect(page.getByRole("button", { name: "拉取模型" })).toBeVisible();
  await expect(page.getByRole("button", { name: "保存并测试" })).toBeVisible();
  await expect(page.getByText("career-collector start", { exact: true })).toBeVisible();
  await expect(page.locator(".sidebar-note")).not.toHaveText("Demo Provider");
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: testInfo.outputPath("mobile-settings.png"), fullPage: true });
});

test("keeps application board scrolling inside its workspace", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/applications");
  await expect(page.getByRole("heading", { name: "投递看板" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: testInfo.outputPath("desktop-applications.png"), fullPage: true });
});
