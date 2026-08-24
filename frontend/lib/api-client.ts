// Thin typed wrapper around the FastAPI backend (see backend/app/api/).
// No caching/retry layer yet -- add one if/when a real usage pattern
// actually needs it, not preemptively.

import type { Assessment, AnswerIn, AnswerOut, Finding, Question, Report } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response body wasn't JSON -- keep the statusText fallback
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getQuestions: (adapterId: string) => request<Question[]>(`/adapters/${adapterId}/questions`),

  createAssessment: (adapterId: string, subjectLabel: string) =>
    request<Assessment>("/assessments", {
      method: "POST",
      body: JSON.stringify({ adapter_id: adapterId, subject_label: subjectLabel }),
    }),

  getAssessment: (runId: string) => request<Assessment>(`/assessments/${runId}`),

  upsertAnswer: (runId: string, indicatorId: string, answer: AnswerIn) =>
    request<AnswerOut>(`/assessments/${runId}/answers/${indicatorId}`, {
      method: "PUT",
      body: JSON.stringify(answer),
    }),

  completeAssessment: (runId: string) =>
    request<Assessment>(`/assessments/${runId}/complete`, { method: "POST" }),

  getReport: (runId: string) => request<Report>(`/assessments/${runId}/report`),

  regenerateFinding: (runId: string, indicatorId: string) =>
    request<Finding>(`/assessments/${runId}/findings/${indicatorId}/regenerate`, { method: "POST" }),
};

export { ApiError };
