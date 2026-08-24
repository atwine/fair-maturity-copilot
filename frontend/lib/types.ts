// Mirrors backend/app/api/schemas.py exactly -- if that file changes, this
// must change with it. No codegen yet (fine at this size); revisit if the
// API surface grows much further.

export type AnswerValue = "yes" | "partial" | "no" | "dont_know";

export interface AnswerOption {
  value: AnswerValue;
  label: string;
}

export interface Question {
  indicator_id: string;
  title: string;
  plain_language_question: string;
  help_text: string;
  priority: "essential" | "important" | "useful";
  display_order: number;
  options: AnswerOption[];
}

export interface AnswerIn {
  value: AnswerValue;
  label: string;
  note?: string | null;
}

export interface AnswerOut {
  indicator_id: string;
  value: AnswerValue;
  label: string;
  note: string | null;
  is_dont_know: boolean;
}

export interface Assessment {
  id: string;
  adapter_id: string;
  subject_label: string;
  status: "in_progress" | "completed";
  created_at: string;
  completed_at: string | null;
  answered_indicator_ids: string[];
  answers: AnswerOut[];
}

export interface Finding {
  indicator_id: string;
  title: string;
  severity: "pass" | "minor_gap" | "major_gap" | "unknown";
  remediation_text: string | null;
}

export interface Report {
  run_id: string;
  score: number;
  generated_at: string;
  findings: Finding[];
  markdown: string;
}
