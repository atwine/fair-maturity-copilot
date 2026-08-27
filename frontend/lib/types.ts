// Mirrors backend/app/api/schemas.py exactly -- if that file changes, this
// must change with it. No codegen yet (fine at this size); revisit if the
// API surface grows much further.

// "not_started" (issue #16): a 5th value, offered only by adapters whose
// content actually has an honest "haven't begun this practice yet" state
// (harmonization-v0) -- fair-v0's 12 questions still only ever send the
// original 4. Kept in one shared union rather than per-adapter types since
// the backend's severity vocabulary (below) is genuinely shared across
// adapters by convention, not adapter-specific the way PrincipleGroup is.
export type AnswerValue = "yes" | "partial" | "no" | "dont_know" | "not_started";

export interface AnswerOption {
  value: AnswerValue;
  label: string;
}

// Adapter-defined free text (opaque to the engine, see
// backend/app/api/schemas.py's QuestionOut.principle_group comment) -- not
// a closed union, since a second adapter (harmonization-v0) has its own
// group names, e.g. "Consistent Naming", distinct from fair-v0's 4.
export type PrincipleGroup = string;

export interface Question {
  indicator_id: string;
  title: string;
  plain_language_question: string;
  help_text: string;
  example: string;
  priority: "essential" | "important" | "useful";
  principle_group: PrincipleGroup;
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
  // "not_started" (issue #16): a genuinely neutral outcome, excluded from
  // the score entirely (backend/app/engine/scoring.py) -- only ever
  // produced by an adapter whose content offers that answer value.
  severity: "pass" | "minor_gap" | "major_gap" | "unknown" | "not_started";
  principle_group: PrincipleGroup;
  remediation_text: string | null;
}

export interface Report {
  run_id: string;
  score: number;
  generated_at: string;
  findings: Finding[];
  markdown: string;
}

export interface PlanIndicatorRef {
  indicator_id: string;
  title: string;
  principle_group: PrincipleGroup;
}

export interface PlanStep {
  id: string;
  title: string;
  detail: string;
  indicators: PlanIndicatorRef[];
}

export interface Plan {
  run_id: string;
  goal: string;
  steps: PlanStep[];
}

export type SkillLevel = "new_to_this" | "done_this_before";

export interface MentorMessage {
  role: "user" | "mentor";
  content: string;
  created_at: string;
}

export interface MentorConversation {
  step_id: string;
  skill_level: SkillLevel;
  indicators: PlanIndicatorRef[];
  messages: MentorMessage[];
}

export interface MentorAction {
  indicator_id: string;
  new_value: AnswerValue;
  new_severity: Finding["severity"];
  new_score: number;
}

export interface MentorReply {
  mentor_message: MentorMessage;
  action_taken: MentorAction | null;
}
