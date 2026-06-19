import { api } from "./client";
import type {
  Assessment,
  AssessmentResult,
  Department,
  Enrollment,
  EmployeeReport,
  MyAttendance,
  Notification,
  OrgReport,
  Paginated,
  PerformanceInsight,
  QuestionPublic,
  Training,
  TrainerReport,
  TrainingSession,
  User,
} from "../types";

// --- Auth ---
export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }).then((r) => r.data),
  me: () => api.get<User>("/auth/me").then((r) => r.data),
};

// --- Departments ---
export const departmentsApi = {
  list: () => api.get<Department[]>("/departments").then((r) => r.data),
  create: (body: { name: string; description?: string }) =>
    api.post<Department>("/departments", body).then((r) => r.data),
  update: (id: number, body: Partial<Department>) =>
    api.patch<Department>(`/departments/${id}`, body).then((r) => r.data),
  remove: (id: number) => api.delete(`/departments/${id}`).then((r) => r.data),
};

// --- Users ---
export interface UserQuery {
  role?: string;
  department_id?: number;
  search?: string;
  page?: number;
  size?: number;
}
export const usersApi = {
  list: (q: UserQuery = {}) =>
    api.get<Paginated<User>>("/users", { params: q }).then((r) => r.data),
  get: (id: number) => api.get<User>(`/users/${id}`).then((r) => r.data),
  create: (body: Record<string, unknown>) =>
    api.post<User>("/users", body).then((r) => r.data),
  update: (id: number, body: Record<string, unknown>) =>
    api.patch<User>(`/users/${id}`, body).then((r) => r.data),
  remove: (id: number) => api.delete(`/users/${id}`).then((r) => r.data),
};

// --- Trainings + Enrollments ---
export interface TrainingQuery {
  status?: string;
  department_id?: number;
  search?: string;
  page?: number;
  size?: number;
}
export const trainingsApi = {
  list: (q: TrainingQuery = {}) =>
    api.get<Paginated<Training>>("/trainings", { params: q }).then((r) => r.data),
  get: (id: number) => api.get<Training>(`/trainings/${id}`).then((r) => r.data),
  create: (body: Record<string, unknown>) =>
    api.post<Training>("/trainings", body).then((r) => r.data),
  update: (id: number, body: Record<string, unknown>) =>
    api.patch<Training>(`/trainings/${id}`, body).then((r) => r.data),
  remove: (id: number) => api.delete(`/trainings/${id}`).then((r) => r.data),
  enrollments: (id: number) =>
    api.get<Enrollment[]>(`/trainings/${id}/enrollments`).then((r) => r.data),
  enroll: (id: number, userIds: number[]) =>
    api.post<Enrollment[]>(`/trainings/${id}/enrollments`, { user_ids: userIds }).then((r) => r.data),
  unenroll: (id: number, userId: number) =>
    api.delete(`/trainings/${id}/enrollments/${userId}`).then((r) => r.data),
};

// --- Sessions ---
export const sessionsApi = {
  list: (trainingId?: number) =>
    api
      .get<TrainingSession[]>("/sessions", { params: { training_id: trainingId } })
      .then((r) => r.data),
  create: (body: Record<string, unknown>) =>
    api.post<TrainingSession>("/sessions", body).then((r) => r.data),
  update: (id: number, body: Record<string, unknown>) =>
    api.patch<TrainingSession>(`/sessions/${id}`, body).then((r) => r.data),
  remove: (id: number) => api.delete(`/sessions/${id}`).then((r) => r.data),
  end: (id: number) => api.post<TrainingSession>(`/sessions/${id}/end`).then((r) => r.data),
};

// --- QR attendance ---
export interface QrToken {
  token: string;
  checkin_url: string;
  qr_png_base64: string;
  expires_at: string;
  session_id: number;
}
export const qrApi = {
  generate: (sessionId: number) =>
    api.post<QrToken>(`/sessions/${sessionId}/qr`).then((r) => r.data),
  get: (sessionId: number) =>
    api.get<QrToken>(`/sessions/${sessionId}/qr`).then((r) => r.data),
  revoke: (sessionId: number) =>
    api.delete(`/sessions/${sessionId}/qr`).then((r) => r.data),
};

// --- Courses ---
export const coursesApi = {
  create: (body: Record<string, unknown>) =>
    api.post("/courses", body).then((r) => r.data),
};

// --- Attendance ---
export interface AttendanceEntry {
  user_id: number;
  status: string;
  notes?: string;
}
export const attendanceApi = {
  forSession: (sessionId: number) =>
    api.get(`/attendance`, { params: { session_id: sessionId } }).then((r) => r.data),
  bulk: (sessionId: number, entries: AttendanceEntry[]) =>
    api.post("/attendance/bulk", { session_id: sessionId, entries }).then((r) => r.data),
  mine: () => api.get<MyAttendance[]>("/attendance/me").then((r) => r.data),
  checkin: (token: string) =>
    api.post("/attendance/checkin", { token }).then((r) => r.data),
};

// --- Assessments ---
export const assessmentsApi = {
  list: (trainingId?: number) =>
    api
      .get<Assessment[]>("/assessments", { params: { training_id: trainingId } })
      .then((r) => r.data),
  get: (id: number) => api.get<Assessment>(`/assessments/${id}`).then((r) => r.data),
  create: (body: Record<string, unknown>) =>
    api.post<Assessment>("/assessments", body).then((r) => r.data),
  remove: (id: number) => api.delete(`/assessments/${id}`).then((r) => r.data),
  questions: (id: number) =>
    api.get<QuestionPublic[]>(`/assessments/${id}/questions`).then((r) => r.data),
  submit: (id: number, answers: Record<string, string>, timeTaken?: number) =>
    api
      .post<AssessmentResult>(`/assessments/${id}/submit`, {
        answers,
        time_taken_seconds: timeTaken,
      })
      .then((r) => r.data),
  results: (id: number) =>
    api.get<AssessmentResult[]>(`/assessments/${id}/results`).then((r) => r.data),
  myResults: () =>
    api.get<AssessmentResult[]>("/assessments/me/results").then((r) => r.data),
};

// --- AI ---
export const aiApi = {
  generateAssessment: (body: Record<string, unknown>) =>
    api.post<Assessment>("/ai/generate-assessment", body).then((r) => r.data),
  analyzePerformance: (userId: number) =>
    api
      .post<PerformanceInsight>("/ai/analyze-performance", { user_id: userId })
      .then((r) => r.data),
};

// --- Reports ---
export const reportsApi = {
  org: () => api.get<OrgReport>("/reports/org").then((r) => r.data),
  trainer: (id: number) =>
    api.get<TrainerReport>(`/reports/trainer/${id}`).then((r) => r.data),
  employee: (id: number) =>
    api.get<EmployeeReport>(`/reports/employee/${id}`).then((r) => r.data),
};

// --- Notifications ---
export const notificationsApi = {
  list: (unreadOnly = false) =>
    api
      .get<Notification[]>("/notifications", { params: { unread_only: unreadOnly } })
      .then((r) => r.data),
  markRead: (id: number) => api.post(`/notifications/${id}/read`).then((r) => r.data),
  readAll: () => api.post("/notifications/read-all").then((r) => r.data),
};

// --- Integrations ---
export const integrationsApi = {
  lmsSync: () => api.post("/integrations/lms/sync").then((r) => r.data),
};
