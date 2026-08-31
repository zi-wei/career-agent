export type JobVersion = {
  id: string;
  ordinal: number;
  content_hash: string;
  version_hash: string;
  description: string;
  detail_status: string;
  snapshot: Record<string, unknown>;
};

export type SelectionState = "strengthen" | "skip" | "already_have" | "unselected";

export type JobRequirement = {
  id: string;
  label: string;
  category: string;
  evidence_text: string;
  selection: SelectionState;
};

export type JobDetail = {
  id: string;
  source: string;
  source_job_id: string;
  title: string;
  company: string;
  city: string | null;
  is_saved: boolean;
  current_version: JobVersion;
  versions: JobVersion[];
  requirements: JobRequirement[];
};

export type JobList = { items: JobDetail[] };

export type ProfileFact = { id?: string; kind: string; title: string; content: string };
export type WorkspaceProfile = {
  id: string;
  target_role: string;
  cities: string[];
  availability: string;
  raw_resume: string;
  facts: ProfileFact[];
};

export type ResumeBullet = { text: string; source_refs: string[] };
export type ResumeSection = {
  kind: string;
  title: string;
  bullets: ResumeBullet[];
};
export type Resume = {
  id: string;
  root_id: string;
  previous_revision_id: string | null;
  job_version_id: string;
  revision: number;
  status: string;
  target_title: string;
  summary: string;
  sections: ResumeSection[];
};
export type InterviewPack = {
  id: string;
  job_version_id: string;
  revision: number;
  status: string;
  title: string;
  questions: Array<{
    question: string;
    category: string;
    requirement_id: string;
    evidence_text: string;
    answer_guide: string;
  }>;
};
export type MaterialBundle = { job_id: string; resume: Resume; interview_pack: InterviewPack };

export type RollingPlan = {
  id: string;
  job_version_id: string;
  revision: number;
  status: string;
  timezone: string;
  starts_on: string;
  days: Array<{
    day_number: number;
    date: string;
    tasks: Array<{
      id: string;
      kind: string;
      title: string;
      objective: string;
      completion_condition: string;
      requirement_id: string | null;
      status: string;
    }>;
  }>;
};

export type PracticeTask = {
  id: string; plan_id: string; plan_task_id: string; job_version_id: string;
  requirement_ids: string[]; kind: string; title: string; objective: string;
  instructions: string; acceptance_criteria: string[]; deliverables: string[];
  guidance: KnowledgeGuidance | ProjectGuidance | GeneralGuidance;
  status: string; updated_at: string;
};
export type KnowledgeGuidance = {
  explanation: string;
  key_concepts: Array<{ name: string; explanation: string }>;
  scenario_question: string;
  answer_framework: string[];
  self_checks: string[];
};
export type ProjectGuidance = {
  business_context: string;
  milestones: Array<{ title: string; actions: string[]; expected_output: string }>;
  acceptance_criteria: string[];
  deliverables: string[];
  reflection_questions: string[];
};
export type GeneralGuidance = { instructions: string; checklist: string[] };
export type PracticeSubmission = {
  id: string; task_id: string; content: string; artifact_refs: string[];
  report_summary: string; status: string; created_at: string;
};
export type PracticeEvaluation = {
  id: string; submission_id: string; advisory: boolean; summary: string;
  strengths: string[]; improvements: string[]; created_at: string;
};
export type EvidenceItem = {
  id: string; job_version_id: string | null; requirement_ids: string[];
  source_type: string; source_id: string; title: string; description: string;
  verification_level: string; created_at: string;
};
export type ApplicationStatus = "lead" | "planned" | "applied" | "contacted" |
  "interview" | "offer" | "rejected" | "silent" | "withdrawn";
export type Application = {
  id: string; job_id: string; job_version_id: string; resume_id: string;
  status: ApplicationStatus; channel: string; notes: string;
  history: Array<{ status: ApplicationStatus; note: string; created_at: string }>;
  created_at: string; updated_at: string;
};
export type RuntimeStatus = {
  provider: string;
  model: string;
  model_configured: boolean;
  collector_sync_enabled: boolean;
};

export type CollectorTask = {
  id: string;
  source: string;
  keyword: string;
  city: string;
  requested_limit: number;
  status: string;
  captured_count: number;
  version_count: number;
  pending_sync_count: number;
  reason_code: string | null;
  resume_state: string | null;
};

export type CollectorStatusView = {
  companion: { status: string };
  worker: { status: string; pid: number | null };
  login: { status: string; pid: number | null; code?: string };
  task: CollectorTask | null;
};

export type CollectorTaskResult = { status: string; task: CollectorTask };
export type CollectorCity = { name: string; code: string; pinyin: string };

export type ModelSettings = {
  provider: string;
  base_url: string;
  model: string;
  api_key_configured: boolean;
};

export type ModelConnectionInput = {
  base_url: string;
  api_key?: string;
};

export type ModelSettingsInput = ModelConnectionInput & { model: string };

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
  ) {
    super(code);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const code = body?.detail?.code ?? "request_failed";
    throw new ApiError(response.status, code);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

const collectorBaseUrl = "http://127.0.0.1:8765/v1";

async function collectorRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${collectorBaseUrl}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) throw new Error("collector_request_failed");
  return response.json() as Promise<T>;
}

export const collectorApi = {
  status: () => collectorRequest<CollectorStatusView>("/status"),
  cities: () => collectorRequest<{ items: CollectorCity[] }>("/cities"),
  createTask: (payload: { source: "boss"; keyword: string; city: string; limit: number }) =>
    collectorRequest<CollectorTaskResult>("/tasks", { method: "POST", body: JSON.stringify(payload) }),
  pause: () => collectorRequest<CollectorTaskResult>("/tasks/latest/pause", { method: "POST", body: "{}" }),
  resume: () => collectorRequest<CollectorTaskResult>("/tasks/latest/resume", { method: "POST", body: "{}" }),
  login: () => collectorRequest<{ status: string; pid: number | null }>("/login", { method: "POST", body: "{}" }),
};

export const workspaceApi = {
  get: () => request<WorkspaceProfile>("/api/workspace/profile"),
  update: (profile: Omit<WorkspaceProfile, "id">) =>
    request<WorkspaceProfile>("/api/workspace/profile", {
      method: "PUT",
      body: JSON.stringify(profile),
    }),
};

export const runtimeApi = {
  get: () => request<RuntimeStatus>("/api/runtime"),
};

export const modelSettingsApi = {
  get: () => request<ModelSettings>("/api/model-settings"),
  models: (payload: ModelConnectionInput) =>
    request<{ items: string[] }>("/api/model-settings/models", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  update: (payload: ModelSettingsInput) =>
    request<ModelSettings>("/api/model-settings", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  test: (payload: ModelSettingsInput) =>
    request<{ status: string; model: string; latency_ms: number }>("/api/model-settings/test", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

export const jobsApi = {
  list: () => request<JobList>("/api/jobs"),
  clear: () => request<{ deleted_count: number }>("/api/jobs", { method: "DELETE" }),
  updateSaved: (jobId: string, saved: boolean) =>
    request<JobDetail>(`/api/jobs/${jobId}/saved`, {
      method: "PUT",
      body: JSON.stringify({ saved }),
    }),
  remove: (jobId: string) => request<void>(`/api/jobs/${jobId}`, { method: "DELETE" }),
  batchAction: (jobIds: string[], action: "save" | "unsave" | "delete") =>
    request<{ affected_count: number }>("/api/jobs/batch-actions", {
      method: "POST",
      body: JSON.stringify({ job_ids: jobIds, action }),
    }),
  get: (jobId: string) => request<JobDetail>(`/api/jobs/${jobId}`),
  paste: (payload: { title: string; company: string; description: string; city?: string }) =>
    request<JobDetail>("/api/jobs/paste", { method: "POST", body: JSON.stringify(payload) }),
  importJson: (payload: unknown) =>
    request<JobDetail>("/api/jobs/import", { method: "POST", body: JSON.stringify(payload) }),
};

export const materialsApi = {
  latest: (jobId: string) => request<MaterialBundle>(`/api/jobs/${jobId}/materials/latest`),
  generate: (jobId: string) =>
    request<MaterialBundle>(`/api/jobs/${jobId}/materials`, { method: "POST" }),
  revise: (resumeId: string, payload: { summary: string; sections: ResumeSection[] }) =>
    request<Resume>(`/api/materials/resumes/${resumeId}/revisions`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  exportUrl: (resumeId: string) =>
    `/api/materials/resumes/${resumeId}/export?format=markdown`,
};

export const planningApi = {
  updateSelections: (
    jobId: string,
    selections: Array<{ requirement_id: string; state: SelectionState }>,
  ) =>
    request<{ items: Array<{ requirement_id: string; state: SelectionState }> }>(
      `/api/jobs/${jobId}/selections`,
      { method: "PUT", body: JSON.stringify({ selections }) },
    ),
  createPlan: (jobId: string) =>
    request<RollingPlan>(`/api/jobs/${jobId}/plans`, { method: "POST" }),
  latestPlan: (jobId: string) => request<RollingPlan>(`/api/jobs/${jobId}/plans/latest`),
};

export const practiceApi = {
  list: () => request<{ items: PracticeTask[] }>("/api/practice/tasks"),
  remove: (taskId: string) => request<void>(`/api/practice/tasks/${taskId}`, { method: "DELETE" }),
  fromPlan: (planId: string) => request<{ items: PracticeTask[] }>(
    `/api/practice/tasks/from-plan/${planId}`, { method: "POST" },
  ),
  start: (taskId: string) => request<PracticeTask>(
    `/api/practice/tasks/${taskId}/start`, { method: "POST" },
  ),
  submit: (taskId: string, payload: { content: string; artifact_refs: string[]; report_summary: string }) =>
    request<PracticeSubmission>(`/api/practice/tasks/${taskId}/submissions`, {
      method: "POST", body: JSON.stringify(payload),
    }),
  evaluate: (submissionId: string) => request<PracticeEvaluation>(
    `/api/practice/submissions/${submissionId}/evaluate`, { method: "POST" },
  ),
};

export const evidenceApi = {
  list: () => request<{ items: EvidenceItem[] }>("/api/evidence"),
  remove: (evidenceId: string) => request<void>(`/api/evidence/${evidenceId}`, { method: "DELETE" }),
};

export const applicationsApi = {
  list: () => request<{ items: Application[] }>("/api/applications"),
  create: (payload: { job_id: string; resume_id: string; channel: string; notes: string }) =>
    request<Application>("/api/applications", { method: "POST", body: JSON.stringify(payload) }),
  updateStatus: (applicationId: string, status: ApplicationStatus, note: string) =>
    request<Application>(`/api/applications/${applicationId}/status`, {
      method: "POST", body: JSON.stringify({ status, note }),
    }),
  addFeedback: (applicationId: string, payload: {
    stage: string; outcome: string; question: string; recorded_reason: string; notes: string;
  }) => request(`/api/applications/${applicationId}/feedback`, {
    method: "POST", body: JSON.stringify(payload),
  }),
  advice: (applicationId: string) => request<{
    summary: string; source_facts: string[]; next_actions: string[];
  }>(`/api/applications/${applicationId}/advice`, { method: "POST" }),
};
