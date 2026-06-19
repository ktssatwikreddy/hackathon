import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  type AttendanceEntry,
  type TrainingQuery,
  type UserQuery,
  assessmentsApi,
  attendanceApi,
  departmentsApi,
  notificationsApi,
  reportsApi,
  sessionsApi,
  trainingsApi,
  usersApi,
} from "./api/resources";

// --- Departments ---
export const useDepartments = () =>
  useQuery({ queryKey: ["departments"], queryFn: departmentsApi.list });

export const useDepartmentMutations = () => {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ["departments"] });
  return {
    create: useMutation({ mutationFn: departmentsApi.create, onSuccess: invalidate }),
    update: useMutation({
      mutationFn: (v: { id: number; body: Record<string, unknown> }) =>
        departmentsApi.update(v.id, v.body),
      onSuccess: invalidate,
    }),
    remove: useMutation({ mutationFn: departmentsApi.remove, onSuccess: invalidate }),
  };
};

// --- Users ---
export const useUsers = (q: UserQuery) =>
  useQuery({ queryKey: ["users", q], queryFn: () => usersApi.list(q) });

export const useUserMutations = () => {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ["users"] });
  return {
    create: useMutation({ mutationFn: usersApi.create, onSuccess: invalidate }),
    update: useMutation({
      mutationFn: (v: { id: number; body: Record<string, unknown> }) =>
        usersApi.update(v.id, v.body),
      onSuccess: invalidate,
    }),
    remove: useMutation({ mutationFn: usersApi.remove, onSuccess: invalidate }),
  };
};

// --- Trainings ---
export const useTrainings = (q: TrainingQuery) =>
  useQuery({ queryKey: ["trainings", q], queryFn: () => trainingsApi.list(q) });

export const useTraining = (id: number) =>
  useQuery({ queryKey: ["training", id], queryFn: () => trainingsApi.get(id), enabled: !!id });

export const useEnrollments = (id: number) =>
  useQuery({
    queryKey: ["enrollments", id],
    queryFn: () => trainingsApi.enrollments(id),
    enabled: !!id,
  });

export const useTrainingMutations = () => {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ["trainings"] });
  return {
    create: useMutation({ mutationFn: trainingsApi.create, onSuccess: invalidate }),
    update: useMutation({
      mutationFn: (v: { id: number; body: Record<string, unknown> }) =>
        trainingsApi.update(v.id, v.body),
      onSuccess: invalidate,
    }),
    remove: useMutation({ mutationFn: trainingsApi.remove, onSuccess: invalidate }),
    enroll: useMutation({
      mutationFn: (v: { id: number; userIds: number[] }) =>
        trainingsApi.enroll(v.id, v.userIds),
      onSuccess: (_d, v) => qc.invalidateQueries({ queryKey: ["enrollments", v.id] }),
    }),
    unenroll: useMutation({
      mutationFn: (v: { id: number; userId: number }) =>
        trainingsApi.unenroll(v.id, v.userId),
      onSuccess: (_d, v) => qc.invalidateQueries({ queryKey: ["enrollments", v.id] }),
    }),
  };
};

// --- Sessions ---
export const useSessions = (trainingId?: number) =>
  useQuery({ queryKey: ["sessions", trainingId], queryFn: () => sessionsApi.list(trainingId) });

export const useSessionMutations = () => {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ["sessions"] });
  return {
    create: useMutation({ mutationFn: sessionsApi.create, onSuccess: invalidate }),
    update: useMutation({
      mutationFn: (v: { id: number; body: Record<string, unknown> }) =>
        sessionsApi.update(v.id, v.body),
      onSuccess: invalidate,
    }),
    remove: useMutation({ mutationFn: sessionsApi.remove, onSuccess: invalidate }),
  };
};

// --- Attendance ---
export const useMyAttendance = () =>
  useQuery({ queryKey: ["attendance", "me"], queryFn: attendanceApi.mine });

export const useMarkAttendance = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (v: { sessionId: number; entries: AttendanceEntry[] }) =>
      attendanceApi.bulk(v.sessionId, v.entries),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["attendance"] }),
  });
};

// --- Assessments ---
export const useAssessments = (trainingId?: number) =>
  useQuery({ queryKey: ["assessments", trainingId], queryFn: () => assessmentsApi.list(trainingId) });

export const useMyResults = () =>
  useQuery({ queryKey: ["assessments", "me", "results"], queryFn: assessmentsApi.myResults });

// --- Reports ---
export const useOrgReport = (enabled: boolean) =>
  useQuery({ queryKey: ["report", "org"], queryFn: reportsApi.org, enabled });

export const useTrainerReport = (id: number, enabled: boolean) =>
  useQuery({ queryKey: ["report", "trainer", id], queryFn: () => reportsApi.trainer(id), enabled });

export const useEmployeeReport = (id: number, enabled: boolean) =>
  useQuery({ queryKey: ["report", "employee", id], queryFn: () => reportsApi.employee(id), enabled });

// --- Notifications ---
export const useNotifications = (unreadOnly = false) =>
  useQuery({ queryKey: ["notifications", unreadOnly], queryFn: () => notificationsApi.list(unreadOnly) });

export const useNotificationMutations = () => {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ["notifications"] });
  return {
    markRead: useMutation({ mutationFn: notificationsApi.markRead, onSuccess: invalidate }),
    readAll: useMutation({ mutationFn: notificationsApi.readAll, onSuccess: invalidate }),
  };
};
