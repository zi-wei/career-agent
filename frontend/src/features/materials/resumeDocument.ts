import type { ResumeSection } from "../../api/client";

export type ResumePersonalDetails = {
  name: string;
  headline: string;
  basicInfo: string[];
  contacts: string[];
  honors: string[];
  avatarDataUrl: string;
};

export type ResumeDocumentInput = {
  personal: ResumePersonalDetails;
  summary: string;
  sections: ResumeSection[];
};

const sectionIcons: Record<string, string> = {
  education: "🎓",
  experience: "💼",
  work: "💼",
  project: "🛠",
  skills: "💡",
  skill: "💡",
  summary: "🧠",
};

function escapeHtml(value: string) {
  return value.replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]!);
}

function safeAvatar(value: string) {
  return /^data:image\/(?:png|jpeg|webp);base64,[a-z0-9+/=]+$/i.test(value)
    ? escapeHtml(value)
    : "";
}

function editableList(items: string[]) {
  return items.map((item) => `<li contenteditable="true">${escapeHtml(item)}</li>`).join("");
}

function sectionHtml(section: ResumeSection) {
  const icon = sectionIcons[section.kind.toLowerCase()] ?? "▦";
  const bullets = section.bullets.map((bullet) => `
    <article class="resume-item">
      <p contenteditable="true">${escapeHtml(bullet.text)}</p>
    </article>`).join("");
  return `
    <section class="resume-section">
      <h2><span aria-hidden="true">${icon}</span>${escapeHtml(section.title)}</h2>
      ${bullets}
    </section>`;
}

export function buildResumeHtml({ personal, summary, sections }: ResumeDocumentInput) {
  const avatar = safeAvatar(personal.avatarDataUrl);
  const avatarMarkup = avatar
    ? `<img id="avatarPreview" src="${avatar}" alt="头像">`
    : `<div id="avatarFallback" class="avatar-fallback">${escapeHtml(personal.name.trim().slice(0, 1) || "照")}</div>`;
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(personal.name || "针对性简历")}</title>
  <style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&display=swap");
    :root { --accent: #76b900; --paper: #fff; --soft: #fafafa; --text: #20251f; --muted: #687066; }
    * { box-sizing: border-box; }
    body { margin: 0; background: #edf0eb; color: var(--text); font-family: "Noto Sans SC", sans-serif; line-height: 1.6; }
    .document-actions { position: sticky; top: 0; z-index: 2; display: flex; justify-content: center; gap: 10px; padding: 12px; background: rgba(255,255,255,.96); border-bottom: 1px solid #dfe3dc; }
    button, .upload-label { padding: 8px 14px; border: 1px solid #cbd2c7; border-radius: 6px; background: #fff; color: var(--text); cursor: pointer; font: inherit; }
    button:hover, .upload-label:hover { border-color: var(--accent); color: #4f7c00; }
    #avatarInput { position: absolute; width: 1px; height: 1px; overflow: hidden; opacity: 0; }
    .resume-page { width: 210mm; min-height: 297mm; display: grid; grid-template-columns: 220px 1fr; margin: 24px auto; overflow: hidden; background: var(--paper); border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.15); }
    .resume-sidebar { padding: 18px; background: #f4f8ef; border-right: 3px solid #f0f0f0; }
    .avatar-wrap { width: 100px; height: 100px; margin: 0 auto 12px; overflow: hidden; border: 3px solid #fff; border-radius: 50%; box-shadow: 0 2px 8px rgba(0,0,0,.12); }
    .avatar-wrap img { width: 100%; height: 100%; object-fit: cover; }
    .avatar-fallback { width: 100%; height: 100%; display: grid; place-items: center; background: #dbe8ce; color: #4f7c00; font-size: 32px; font-weight: 700; }
    .resume-name { margin: 0; text-align: center; font-size: 20px; line-height: 1.35; }
    .resume-headline { margin: 5px 0 18px; color: #4f7c00; text-align: center; font-size: 12px; font-weight: 600; }
    .sidebar-block { margin-top: 16px; background: #fff; border-radius: 8px; overflow: hidden; }
    .sidebar-block h2 { margin: 0; padding: 6px 9px; background: var(--accent); color: #fff; font-size: 12px; }
    .sidebar-block ul { display: grid; gap: 6px; margin: 0; padding: 10px 12px 12px 24px; font-size: 10px; }
    .resume-main { padding: 20px 35px; }
    .resume-summary { margin-bottom: 20px; padding: 10px 15px; background: var(--soft); border-left: 3px solid var(--accent); border-radius: 0 8px 8px 0; font-size: 11px; }
    .resume-section { margin-bottom: 20px; }
    .resume-section h2 { display: flex; align-items: center; gap: 7px; margin: 0 0 10px; padding-bottom: 6px; border-bottom: 1px solid #dbe0d8; color: #4f7c00; font-size: 15px; }
    .resume-item { margin-bottom: 15px; padding: 10px 15px; background: var(--soft); border-left: 3px solid #f0f0f0; border-radius: 0 8px 8px 0; }
    .resume-item p { margin: 0; font-size: 10.5px; }
    [contenteditable="true"]:focus { outline: 1px solid var(--accent); background: #f0fff0; }
    @media (max-width: 840px) {
      .resume-page { width: calc(100% - 24px); min-height: 0; grid-template-columns: 1fr; }
      .resume-sidebar { border-right: 0; border-bottom: 3px solid #f0f0f0; }
      .resume-main { padding: 24px 20px; }
    }
    @media print {
      @page { size: A4; margin: 0; }
      body { background: #fff; }
      .document-actions { display: none !important; }
      .resume-page { width: 210mm; min-height: 297mm; grid-template-columns: 220px 1fr; margin: 0; border-radius: 0; box-shadow: none; }
    }
  </style>
</head>
<body>
  <div class="document-actions">
    <label class="upload-label" for="avatarInput">更换头像</label>
    <input id="avatarInput" type="file" accept="image/png,image/jpeg,image/webp">
    <button id="printButton" type="button">导出为PDF</button>
  </div>
  <main class="resume-page">
    <aside class="resume-sidebar">
      <div class="avatar-wrap">${avatarMarkup}</div>
      <h1 class="resume-name" contenteditable="true">${escapeHtml(personal.name)}</h1>
      <p class="resume-headline" contenteditable="true">${escapeHtml(personal.headline)}</p>
      <section class="sidebar-block"><h2>基本信息</h2><ul>${editableList(personal.basicInfo)}</ul></section>
      <section class="sidebar-block"><h2>联系方式</h2><ul>${editableList(personal.contacts)}</ul></section>
      <section class="sidebar-block"><h2>个人荣誉</h2><ul>${editableList(personal.honors)}</ul></section>
    </aside>
    <div class="resume-main">
      <section class="resume-section"><h2><span aria-hidden="true">🧠</span>自我评价</h2><p class="resume-summary" contenteditable="true">${escapeHtml(summary)}</p></section>
      ${sections.map(sectionHtml).join("")}
    </div>
  </main>
  <script>
    const avatarInput = document.getElementById("avatarInput");
    avatarInput.addEventListener("change", () => {
      const file = avatarInput.files && avatarInput.files[0];
      if (!file || !["image/png", "image/jpeg", "image/webp"].includes(file.type)) return;
      const reader = new FileReader();
      reader.addEventListener("load", () => {
        const wrap = document.querySelector(".avatar-wrap");
        wrap.innerHTML = "";
        const image = document.createElement("img");
        image.id = "avatarPreview";
        image.alt = "头像";
        image.src = String(reader.result);
        wrap.appendChild(image);
      });
      reader.readAsDataURL(file);
    });
    document.getElementById("printButton").addEventListener("click", () => window.print());
  </script>
</body>
</html>`;
}
