import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FileDown, Printer, RefreshCw, Save, Send, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError, applicationsApi, materialsApi } from "../../api/client";
import type { MaterialBundle, ResumeSection } from "../../api/client";
import { useBackgroundTask, useElapsedSeconds } from "../../app/BackgroundTasks";
import { buildResumeHtml } from "./resumeDocument";
import type { ResumePersonalDetails } from "./resumeDocument";
import { ResumeTemplate } from "./ResumeTemplate";

const PERSONAL_DETAILS_KEY = "career-agent.resume-personal-details";

const generationErrorMessages: Record<string, string> = {
  invalid_model_output: "模型返回的材料格式不完整, 请重新生成.",
  invalid_model_response: "模型服务返回了无效响应, 请稍后重新生成.",
  model_temporarily_unavailable: "模型服务暂时不可用, 请稍后重新生成.",
  model_service_unreachable: "无法连接模型服务, 请检查设置后重新生成.",
  unsupported_provider: "当前模型提供方不受支持, 请检查模型设置.",
};

function generationErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return generationErrorMessages[error.code] ?? "材料生成失败, 请稍后重新生成.";
  }
  return "材料生成失败, 请检查网络后重新生成.";
}

function defaultPersonalDetails(): ResumePersonalDetails {
  return {
    name: "点击填写姓名",
    headline: "",
    basicInfo: ["求职意向: 点击填写", "现居: 点击填写", "到岗时间: 点击填写"],
    contacts: ["手机: 点击填写", "邮箱: 点击填写"],
    honors: ["点击补充个人荣誉"],
    avatarDataUrl: "",
  };
}

function loadPersonalDetails() {
  try {
    const stored = window.localStorage.getItem(PERSONAL_DETAILS_KEY);
    if (!stored) return defaultPersonalDetails();
    const value = JSON.parse(stored) as Partial<ResumePersonalDetails>;
    if (
      typeof value.name !== "string"
      || typeof value.headline !== "string"
      || !Array.isArray(value.basicInfo)
      || !Array.isArray(value.contacts)
      || !Array.isArray(value.honors)
      || typeof value.avatarDataUrl !== "string"
    ) return defaultPersonalDetails();
    return value as ResumePersonalDetails;
  } catch {
    return defaultPersonalDetails();
  }
}

function downloadHtmlFile(filename: string, html: string) {
  const url = URL.createObjectURL(new Blob([html], { type: "text/html;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function MaterialsPage() {
  const { jobId = "" } = useParams();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"resume" | "interview">("resume");
  const [summary, setSummary] = useState("");
  const [sections, setSections] = useState<ResumeSection[]>([]);
  const [personal, setPersonal] = useState(loadPersonalDetails);
  const generation = useBackgroundTask<MaterialBundle>(`materials:${jobId}`);
  const elapsedSeconds = useElapsedSeconds(generation.startedAt, generation.isPending);
  const query = useQuery({ queryKey: ["materials", jobId], queryFn: () => materialsApi.latest(jobId) });
  const materials = generation.data ?? query.data;

  useEffect(() => {
    if (!materials) return;
    setSummary(materials.resume.summary);
    setSections(materials.resume.sections);
    setPersonal((current) => current.headline ? current : {
      ...current,
      headline: materials.resume.target_title,
      basicInfo: [
        `求职意向: ${materials.resume.target_title}`,
        "现居: 点击填写",
        "到岗时间: 点击填写",
      ],
    });
  }, [materials]);

  useEffect(() => {
    try {
      window.localStorage.setItem(PERSONAL_DETAILS_KEY, JSON.stringify(personal));
    } catch {
      // The resume remains editable when storage is unavailable or an avatar exceeds quota.
    }
  }, [personal]);

  const generateMaterials = () => generation.run(
    () => materialsApi.generate(jobId),
    {
      label: "生成求职材料",
      onSuccess: (bundle) => { queryClient.setQueryData(["materials", jobId], bundle); },
    },
  ).catch(() => undefined);

  const revise = useMutation({
    mutationFn: () => materialsApi.revise(materials!.resume.id, { summary, sections }),
    onSuccess: (resume) => queryClient.setQueryData<MaterialBundle>(["materials", jobId], (current) => (
      current ? { ...current, resume } : current
    )),
  });

  const application = useMutation({
    mutationFn: () => applicationsApi.create({
      job_id: jobId,
      resume_id: materials!.resume.id,
      channel: "待填写",
      notes: "从求职材料创建",
    }),
  });

  const exportHtml = () => {
    if (!materials) return;
    const html = buildResumeHtml({ personal, summary, sections });
    const filename = `${materials.resume.target_title.replace(/[\\/:*?"<>|]/g, "-")}-简历.html`;
    downloadHtmlFile(filename, html);
  };

  if (query.isLoading && !generation.isPending && !generation.data) {
    return <section className="page"><p className="empty-state">正在读取求职材料</p></section>;
  }

  if (!materials) return (
    <section className="page centered-action material-generation">
      <Sparkles size={30} />
      <h1>生成针对性求职材料</h1>
      <p>系统根据当前JD和你提供的真实经历生成简历草稿与面试题.</p>
      {generation.isPending && (
        <div className="generation-status" aria-live="polite">
          <div className="activity-progress" role="progressbar" aria-label="材料生成进度"><span /></div>
          <p>正在分析JD并生成简历与面试题, 已等待 {elapsedSeconds} 秒.</p>
        </div>
      )}
      {generation.status === "error" && <p className="form-error" role="alert">{generationErrorMessage(generation.error)}</p>}
      <button onClick={() => void generateMaterials()} disabled={generation.isPending}>
        <Sparkles size={17} />
        {generation.isPending ? "正在生成" : generation.status === "error" ? "重新生成" : "生成求职材料"}
      </button>
    </section>
  );

  const bundle = materials;
  return (
    <section className="page materials-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">版本 {bundle.resume.revision}</p>
          <h1>求职材料</h1>
          <p>围绕真实JD生成的针对性简历与面试准备.</p>
          {generation.isPending && <p className="inline-task-progress" role="status">正在后台生成新版本, 已等待 {elapsedSeconds} 秒. 离开页面不会中断.</p>}
          {generation.status === "error" && <p className="form-error" role="alert">{generationErrorMessage(generation.error)}</p>}
        </div>
        <div className="heading-actions">
          <button className="secondary" disabled={generation.isPending} onClick={() => void generateMaterials()}>
            <RefreshCw size={16} />{generation.isPending ? "正在生成" : "重新生成材料"}
          </button>
          <button disabled={revise.isPending} onClick={() => revise.mutate()}>
            <Save size={16} />{revise.isPending ? "正在保存" : "保存为新版本"}
          </button>
        </div>
      </div>
      <div className="tabs">
        <button className={tab === "resume" ? "active" : ""} onClick={() => setTab("resume")}>针对性简历</button>
        <button className={tab === "interview" ? "active" : ""} onClick={() => setTab("interview")}>面试题</button>
      </div>
      {tab === "resume" ? (
        <>
          <div className="resume-toolbar no-print">
            <a className="button-link secondary" href={materialsApi.exportUrl(bundle.resume.id)}><Download size={16} />Markdown</a>
            <button className="secondary" onClick={exportHtml}><FileDown size={16} />下载HTML</button>
            <button className="secondary" onClick={() => window.print()}><Printer size={16} />导出PDF</button>
          </div>
          <ResumeTemplate
            key={bundle.resume.id}
            personal={personal}
            summary={summary}
            sections={sections}
            onPersonalChange={setPersonal}
            onSummaryChange={setSummary}
            onSectionsChange={setSections}
          />
        </>
      ) : (
        <div className="question-list">
          {bundle.interview_pack.questions.map((question, index) => (
            <article key={`${question.requirement_id}-${index}`}>
              <span>问题 {index + 1}</span><h2>{question.question}</h2><p>{question.answer_guide}</p><blockquote>{question.evidence_text}</blockquote>
            </article>
          ))}
        </div>
      )}
      <div className="footer-action split-action no-print">
        <button className="secondary" onClick={() => application.mutate()}><Send size={16} />加入投递看板</button>
        <Link className="button-link" to={`/jobs/${jobId}/selection`}>下一步: 选择加强项</Link>
      </div>
      {revise.isSuccess && <p className="success-message">新版本已保存</p>}
      {application.isSuccess && <p className="success-message">已加入投递看板</p>}
    </section>
  );
}
