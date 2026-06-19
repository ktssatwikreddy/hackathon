import { Navigate, createBrowserRouter } from "react-router-dom";

import AppLayout from "../layouts/AppLayout";
import AIInsights from "../pages/AIInsights";
import Attend from "../pages/Attend";
import CourseCreate from "../pages/CourseCreate";
import AssessmentDetail from "../pages/AssessmentDetail";
import Assessments from "../pages/Assessments";
import AttendanceMark from "../pages/AttendanceMark";
import AttendanceMine from "../pages/AttendanceMine";
import Dashboard from "../pages/Dashboard";
import Departments from "../pages/Departments";
import Login from "../pages/Login";
import NotFound from "../pages/NotFound";
import Notifications from "../pages/Notifications";
import Profile from "../pages/Profile";
import Reports from "../pages/Reports";
import Sessions from "../pages/Sessions";
import TrainingDetail from "../pages/TrainingDetail";
import Trainings from "../pages/Trainings";
import Users from "../pages/Users";
import ProtectedRoute from "./ProtectedRoute";

export const router = createBrowserRouter([
  { path: "/login", element: <Login /> },
  { path: "/attend/:token", element: <Attend /> },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Dashboard /> },
      { path: "users", element: <ProtectedRoute roles={["super_admin"]}><Users /></ProtectedRoute> },
      { path: "departments", element: <ProtectedRoute roles={["super_admin"]}><Departments /></ProtectedRoute> },
      { path: "courses/new", element: <ProtectedRoute roles={["super_admin"]}><CourseCreate /></ProtectedRoute> },
      { path: "trainings", element: <Trainings /> },
      { path: "trainings/:id", element: <TrainingDetail /> },
      { path: "sessions", element: <ProtectedRoute roles={["super_admin", "trainer"]}><Sessions /></ProtectedRoute> },
      { path: "attendance/mark", element: <ProtectedRoute roles={["super_admin", "trainer"]}><AttendanceMark /></ProtectedRoute> },
      { path: "attendance/mine", element: <AttendanceMine /> },
      { path: "assessments", element: <Assessments /> },
      { path: "assessments/:id", element: <AssessmentDetail /> },
      { path: "ai", element: <AIInsights /> },
      { path: "reports", element: <Reports /> },
      { path: "notifications", element: <Notifications /> },
      { path: "profile", element: <Profile /> },
    ],
  },
  { path: "404", element: <NotFound /> },
  { path: "*", element: <Navigate to="/404" replace /> },
]);
