import {
  CheckCircle,
  EmojiEvents,
  Groups,
  HowToReg,
  MenuBook,
  School,
} from "@mui/icons-material";
import { Box, Card, CardContent, CircularProgress, Grid, Typography } from "@mui/material";

import { BarSeries, LineSeries, PieSeries } from "../components/charts";
import StatCard from "../components/StatCard";
import { useEmployeeReport, useOrgReport, useTrainerReport } from "../hooks";
import { useAuth } from "../store/auth";

function Loading() {
  return (
    <Box sx={{ display: "grid", placeItems: "center", height: 300 }}>
      <CircularProgress />
    </Box>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>{title}</Typography>
        {children}
      </CardContent>
    </Card>
  );
}

function OrgDashboard() {
  const { data, isLoading } = useOrgReport(true);
  if (isLoading || !data) return <Loading />;
  return (
    <>
      <Grid container spacing={2} mb={1}>
        <Grid item xs={12} sm={6} md={3}><StatCard label="Total Users" value={data.total_users} icon={<Groups />} /></Grid>
        <Grid item xs={12} sm={6} md={3}><StatCard label="Trainings" value={data.total_trainings} icon={<School />} color="#0d9488" /></Grid>
        <Grid item xs={12} sm={6} md={3}><StatCard label="Attendance Rate" value={data.overall_attendance_rate} suffix="%" icon={<HowToReg />} color="#d97706" /></Grid>
        <Grid item xs={12} sm={6} md={3}><StatCard label="Assessment Pass Rate" value={data.assessment_pass_rate} suffix="%" icon={<EmojiEvents />} color="#16a34a" /></Grid>
      </Grid>
      <Grid container spacing={2}>
        <Grid item xs={12} md={4}><ChartCard title="Trainings by Status"><PieSeries data={data.trainings_by_status} /></ChartCard></Grid>
        <Grid item xs={12} md={4}><ChartCard title="Enrollments by Department"><BarSeries data={data.enrollments_by_department} /></ChartCard></Grid>
        <Grid item xs={12} md={4}><ChartCard title="Attendance by Status"><BarSeries data={data.attendance_by_status} /></ChartCard></Grid>
      </Grid>
    </>
  );
}

function TrainerDashboard({ userId }: { userId: number }) {
  const { data, isLoading } = useTrainerReport(userId, true);
  if (isLoading || !data) return <Loading />;
  return (
    <>
      <Grid container spacing={2} mb={1}>
        <Grid item xs={12} sm={6} md={3}><StatCard label="My Trainings" value={data.trainings_count} icon={<School />} /></Grid>
        <Grid item xs={12} sm={6} md={3}><StatCard label="Sessions" value={data.sessions_count} icon={<MenuBook />} color="#0d9488" /></Grid>
        <Grid item xs={12} sm={6} md={3}><StatCard label="Avg Attendance" value={data.avg_attendance_rate} suffix="%" icon={<HowToReg />} color="#d97706" /></Grid>
        <Grid item xs={12} sm={6} md={3}><StatCard label="Avg Score" value={data.avg_assessment_score} suffix="%" icon={<EmojiEvents />} color="#16a34a" /></Grid>
      </Grid>
      <ChartCard title="Enrollments per Training">
        <BarSeries data={data.trainings.map((t) => ({ label: t.title, count: t.enrollment_count }))} />
      </ChartCard>
    </>
  );
}

function EmployeeDashboard({ userId }: { userId: number }) {
  const { data, isLoading } = useEmployeeReport(userId, true);
  if (isLoading || !data) return <Loading />;
  return (
    <>
      <Grid container spacing={2} mb={1}>
        <Grid item xs={12} sm={6} md={3}><StatCard label="Attendance" value={data.attendance_pct} suffix="%" icon={<HowToReg />} /></Grid>
        <Grid item xs={12} sm={6} md={3}><StatCard label="Enrolled" value={data.enrolled_trainings} icon={<School />} color="#0d9488" /></Grid>
        <Grid item xs={12} sm={6} md={3}><StatCard label="Completed" value={data.completed_trainings} icon={<CheckCircle />} color="#16a34a" /></Grid>
        <Grid item xs={12} sm={6} md={3}><StatCard label="Avg Score" value={data.avg_score} suffix="%" icon={<EmojiEvents />} color="#d97706" /></Grid>
      </Grid>
      <ChartCard title="My Assessment Scores">
        {data.results.length ? (
          <LineSeries
            data={[...data.results].reverse().map((r, i) => ({
              label: r.assessment_title.slice(0, 14) || `#${i + 1}`,
              value: r.max_score ? Math.round((r.score / r.max_score) * 100) : 0,
            }))}
          />
        ) : (
          <Typography color="text.secondary">No assessment attempts yet.</Typography>
        )}
      </ChartCard>
    </>
  );
}

export default function Dashboard() {
  const user = useAuth((s) => s.user)!;
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Welcome, {user.name.split(" ")[0]}
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={3}>
        Your {user.role.replace("_", " ")} overview
      </Typography>
      {user.role === "super_admin" && <OrgDashboard />}
      {user.role === "trainer" && <TrainerDashboard userId={user.id} />}
      {user.role === "employee" && <EmployeeDashboard userId={user.id} />}
    </Box>
  );
}
