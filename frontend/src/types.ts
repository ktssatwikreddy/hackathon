// Shared types mirroring the backend Pydantic schemas.

export type Role = "super_admin" | "trainer" | "employee";

export interface User {
  id: number;
  employee_code: string;
  name: string;
  email: string;
  role: Role;
  department_id: number | null;
  phone: string | null;
  designation: string | null;
  joining_date: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Department {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export type TrainingStatus = "draft" | "scheduled" | "active" | "completed" | "cancelled";

export interface Training {
  id: number;
  title: string;
  description: string | null;
  category: string | null;
  trainer_id: number | null;
  department_id: number | null;
  start_date: string | null;
  end_date: string | null;
  capacity: number | null;
  status: TrainingStatus;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface Enrollment {
  id: number;
  user_id: number;
  training_id: number;
  enrolled_on: string;
  status: "enrolled" | "withdrawn" | "completed";
  user?: { id: number; name: string; email: string; employee_code: string } | null;
}

export type SessionMode = "online" | "offline" | "hybrid";

export interface TrainingSession {
  id: number;
  training_id: number;
  title: string;
  session_date: string;
  start_time: string | null;
  end_time: string | null;
  location: string | null;
  mode: SessionMode;
  meeting_link: string | null;
  created_at: string;
}

export type AttendanceStatus = "present" | "absent" | "late" | "excused";

export interface MyAttendance {
  id: number;
  session_id: number;
  session_title: string;
  session_date: string;
  training_id: number;
  training_title: string;
  status: AttendanceStatus;
  marked_at: string;
  notes: string | null;
}

export type QuestionType = "mcq" | "short" | "scenario" | "coding";

export interface Assessment {
  id: number;
  training_id: number;
  title: string;
  description: string | null;
  total_marks: number;
  passing_marks: number;
  duration_minutes: number;
  created_at: string;
  question_count: number;
}

export interface QuestionPublic {
  id: number;
  assessment_id: number;
  question_text: string;
  question_type: QuestionType;
  options: string[] | null;
  marks: number;
  order_index: number;
}

export interface AssessmentResult {
  id: number;
  assessment_id: number;
  user_id: number;
  score: number;
  max_score: number;
  result: "pass" | "fail";
  attempt_date: string;
  time_taken_seconds: number | null;
}

export interface Notification {
  id: number;
  user_id: number;
  title: string;
  message: string;
  type: string;
  link: string | null;
  is_read: boolean;
  created_at: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface LabelCount {
  label: string;
  count: number;
}

export interface OrgReport {
  total_users: number;
  total_trainers: number;
  total_employees: number;
  total_trainings: number;
  active_trainings: number;
  completed_trainings: number;
  total_enrollments: number;
  overall_attendance_rate: number;
  assessment_pass_rate: number;
  trainings_by_status: LabelCount[];
  enrollments_by_department: LabelCount[];
  attendance_by_status: LabelCount[];
}

export interface TrainerReport {
  trainer_id: number;
  name: string;
  trainings_count: number;
  sessions_count: number;
  total_enrollments: number;
  avg_attendance_rate: number;
  assessments_count: number;
  avg_assessment_score: number;
  trainings: { id: number; title: string; status: string; enrollment_count: number }[];
}

export interface EmployeeReport {
  user_id: number;
  name: string;
  attendance_pct: number;
  enrolled_trainings: number;
  completed_trainings: number;
  assessments_taken: number;
  avg_score: number;
  pass_rate: number;
  results: {
    assessment_title: string;
    score: number;
    max_score: number;
    result: "pass" | "fail";
    attempt_date: string;
  }[];
}

export interface PerformanceInsight {
  user_id: number;
  summary: string;
  attendance_pct: number;
  avg_score: number;
  completed_trainings: number;
  learning_gaps: string[];
  skill_areas: string[];
  recommendations: string[];
}
