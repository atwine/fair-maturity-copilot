// Mirrors backend/app/api/schemas.py exactly -- if that file changes, this
// must change with it. No codegen yet (fine at this size); revisit if the
// API surface grows much further.

export type AnswerValue = "yes" | "partial" | "no" | "dont_know";

export interface AnswerOption {
  value: AnswerValue;
  label: string;
}

export type PrincipleGroup = "Findable" | "Accessible" | "Interoperable" | "Reusable";

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
  severity: "pass" | "minor_gap" | "major_gap" | "unknown";
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
  indicator_id: string;
  skill_level: SkillLevel;
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
