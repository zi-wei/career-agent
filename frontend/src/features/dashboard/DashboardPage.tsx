import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Bookmark, Check, FileText, Target, UserRound } from "lucide-react";
import { Link } from "react-router-dom";

import { ApiError, jobsApi, materialsApi, practiceApi, workspaceApi } from "../../api/client";

const completedTaskStates = new Set(["completed", "evaluated"]);

export function DashboardPage() {
  const profile = useQuery({ queryKey: ["profile"], queryFn: workspaceApi.get });
  const jobs = useQuery({ queryKey: ["jobs"], queryFn: jobsApi.list });
  const tasks = useQuery({ queryKey: ["practice"], queryFn: practiceApi.list });
  const savedJobs = jobs.data?.items.filter((item) => item.is_saved) ?? [];
  const primaryJob = savedJobs[0];
  const materials = useQuery({
    queryKey: ["materials", primaryJob?.id],
    queryFn: () => materialsApi.latest(primaryJob!.id),
    enabled: Boolean(primaryJob),
  });

  const isLoading = profile.isLoading || jobs.isLoading || tasks.isLoading || (primaryJob && materials.isLoading);
  const materialsUnexpectedError = materials.error instanceof ApiError
    ? materials.error.status !== 404
    : Boolean(materials.error);
  if (isLoading) return <section className="page"><p className="empty-state">正在整理求职进度</p></section>;
  if (profile.isError || jobs.isError || tasks.isError || materialsUnexpectedError) {
    return <section className="page"><p className="empty-state">暂时无法读取求职进度, 请稍后刷新.</p></section>;
  }

  const profileReady = Boolean(profile.data?.target_role.trim());
  const materialsReady = Boolean(materials.data);
  const taskItems = tasks.data?.items ?? [];
  const pendingTasks = taskItems.filter((item) => !completedTaskStates.has(item.status));
  const completedTasks = taskItems.length - pendingTasks.length;

  let currentStep = 1;
  if (profileReady) currentStep = 2;
  if (profileReady && savedJobs.length > 0) currentStep = 3;
  if (profileReady && savedJobs.length > 0 && materialsReady) currentStep = 4;

  const focus = currentStep === 1
    ? {
        title: "先完成求职档案",
        description: "填写目标岗位、意向城市和真实经历, 后续材料都会以这些信息为依据.",
        path: "/profile",
        action: "完善档案",
      }
    : currentStep === 2
      ? {
          title: "收藏真正想投的职位",
          description: "先采集职位, 再把符合方向的职位收藏为目标, 后续流程只围绕收藏职位展开.",
          path: "/jobs",
          action: "筛选职位",
        }
      : currentStep === 3
        ? {
            title: "为收藏职位生成求职材料",
            description: `从${primaryJob!.title}开始, 生成针对性简历和面试题.`,
            path: `/jobs/${primaryJob!.id}/materials`,
            action: "生成材料",
          }
        : pendingTasks.length > 0
          ? {
              title: "继续完成学习与实训",
              description: `当前任务: ${pendingTasks[0].title}. 完成后提交过程和结果, 沉淀为证据.`,
              path: "/practice",
              action: "继续实训",
            }
          : taskItems.length === 0
            ? {
                title: "开始学习与实训",
                description: "先选择需要加强的岗位要求, 再生成14天学习和实训计划.",
                path: `/jobs/${primaryJob!.id}/selection`,
                action: "制定计划",
              }
            : {
                title: "本轮学习与实训已完成",
                description: "查看已经完成的任务和沉淀证据, 再决定下一轮需要加强的内容.",
                path: "/evidence",
                action: "查看证据",
              };

  const steps = [
    {
      title: "完善档案",
      description: "明确目标岗位, 录入真实经历和可验证事实.",
      detail: profileReady ? profile.data!.target_role : "尚未设置目标岗位",
      icon: UserRound,
    },
    {
      title: "收藏职位",
      description: "采集并筛选真实JD, 收藏准备投递的目标职位.",
      detail: savedJobs.length > 0 ? `${savedJobs.length}个目标职位` : "尚未收藏职位",
      icon: Bookmark,
    },
    {
      title: "生成材料",
      description: "根据收藏职位生成针对性简历和面试题.",
      detail: materialsReady ? "材料已生成" : "等待生成材料",
      icon: FileText,
    },
    {
      title: "学习实训",
      description: "根据材料暴露的岗位要求完成学习、项目和证据沉淀.",
      detail: taskItems.length > 0 ? `${completedTasks}/${taskItems.length}项完成` : "等待制定计划",
      icon: Target,
    },
  ];

  return (
    <section className="page dashboard-page guided-dashboard">
      <header className="dashboard-intro">
        <div>
          <p className="eyebrow">求职工作台</p>
          <h1>从真实职位开始.</h1>
          <p>按顺序完成四步. 首页只提示当前最需要推进的一件事.</p>
        </div>
        <span className="dashboard-step-count">第{currentStep}步 / 共4步</span>
      </header>

      <section className="dashboard-focus" aria-labelledby="focus-title">
        <div>
          <span>现在做这一步</span>
          <h2 id="focus-title">{focus.title}</h2>
          <p>{focus.description}</p>
        </div>
        <Link to={focus.path}>{focus.action}<ArrowRight size={15} aria-hidden="true" /></Link>
      </section>

      <section className="guide-section" aria-labelledby="guide-title">
        <div className="dashboard-section-heading">
          <h2 id="guide-title">完整流程</h2>
          <span>完成一步, 再进入下一步</span>
        </div>
        <ol className="guide-steps">
          {steps.map((step, index) => {
            const stepNumber = index + 1;
            const state = stepNumber < currentStep ? "done" : stepNumber === currentStep ? "current" : "waiting";
            const Icon = step.icon;
            return (
              <li className={state} key={step.title} aria-current={state === "current" ? "step" : undefined}>
                <div className="guide-step-marker">{state === "done" ? <Check size={15} /> : <Icon size={16} />}</div>
                <div className="guide-step-copy">
                  <span>步骤 {stepNumber}</span>
                  <h2>{step.title}</h2>
                  <p>{step.description}</p>
                </div>
                <strong>{step.detail}</strong>
              </li>
            );
          })}
        </ol>
      </section>
    </section>
  );
}
