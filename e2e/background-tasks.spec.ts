import { expect, test } from "@playwright/test";

test("keeps the current job and material generation alive across navigation", async ({ page }) => {
  let finishGeneration!: () => void;
  const generationGate = new Promise<void>((resolve) => { finishGeneration = resolve; });
  const bundle = {
    job_id: "job-background",
    resume: {
      id: "resume-background",
      root_id: "resume-background",
      previous_revision_id: null,
      job_version_id: "version-background",
      revision: 1,
      status: "draft",
      target_title: "Linux 运维实习生",
      summary: "跨页面生成完成",
      sections: [],
    },
    interview_pack: {
      id: "pack-background",
      job_version_id: "version-background",
      revision: 1,
      status: "draft",
      title: "Linux 运维实习生面试题",
      questions: [],
    },
  };

  await page.route("**/api/jobs/job-background/materials**", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 404,
        contentType: "application/json",
        body: JSON.stringify({ detail: { code: "materials_not_found" } }),
      });
      return;
    }
    await generationGate;
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(bundle) });
  });

  await page.goto("/jobs/job-background/materials");
  await page.getByRole("button", { name: "生成求职材料" }).click();
  await expect(page.getByRole("progressbar", { name: "材料生成进度" })).toBeVisible();

  await page.getByRole("link", { name: "求职概览" }).click();
  await expect(page.getByText("当前职位")).toBeVisible();
  await expect(page.getByRole("link", { name: "求职材料" })).toHaveAttribute(
    "href",
    "/jobs/job-background/materials",
  );
  await expect(page.getByText("后台生成中 1 项")).toBeVisible();

  finishGeneration();
  await expect(page.getByText("后台生成中 1 项")).toBeHidden();
  await page.getByRole("link", { name: "求职材料" }).click();
  await expect(page.getByRole("textbox", { name: "简历简介" })).toHaveText("跨页面生成完成");
});
