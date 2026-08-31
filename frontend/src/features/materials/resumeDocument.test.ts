import { describe, expect, it } from "vitest";

import { buildResumeHtml } from "./resumeDocument";

const input = {
  personal: {
    name: "张三",
    headline: "Linux 运维实习生",
    basicInfo: ["现居: 上海", "到岗: 每周5天"],
    contacts: ["手机: 13800000000", "邮箱: user@example.com"],
    honors: ["校级项目实践优秀奖"],
    avatarDataUrl: "",
  },
  summary: "面向 Linux 运维岗位, 具备 Docker 与 Nginx 实践经验.",
  sections: [
    {
      kind: "project",
      title: "项目经历",
      bullets: [
        {
          text: "使用 Docker 部署 Nginx 服务.",
          source_refs: ["profile_fact:fact-1"],
        },
      ],
    },
  ],
};

describe("buildResumeHtml", () => {
  it("builds a standalone editable A4 resume document", () => {
    const html = buildResumeHtml(input);

    expect(html).toContain("width: 210mm");
    expect(html).toContain("min-height: 297mm");
    expect(html).toContain("grid-template-columns: 220px 1fr");
    expect(html).toContain("#76b900");
    expect(html).toContain("Noto+Sans+SC");
    expect(html).toContain('contenteditable="true"');
    expect(html).toContain('id="avatarInput"');
    expect(html).toContain("window.print()");
    expect(html).toContain("@media print");
    expect(html).toContain("Linux 运维实习生");
    expect(html).toContain("使用 Docker 部署 Nginx 服务.");
  });

  it("escapes model and user text before placing it in HTML", () => {
    const html = buildResumeHtml({
      ...input,
      personal: { ...input.personal, name: '<img src=x onerror="alert(1)">' },
      summary: "<script>alert('xss')</script>",
    });

    expect(html).toContain("&lt;img src=x onerror=&quot;alert(1)&quot;&gt;");
    expect(html).toContain("&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;");
    expect(html).not.toContain("<script>alert('xss')</script>");
  });
});
