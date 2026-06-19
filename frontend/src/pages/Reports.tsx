import { Sync } from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Paper,
  Snackbar,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useState } from "react";

import { integrationsApi } from "../api/resources";
import { BarSeries, PieSeries } from "../components/charts";
import RoleGuard from "../components/RoleGuard";
import StatCard from "../components/StatCard";
import { useEmployeeReport, useOrgReport, useTrainerReport } from "../hooks";
import { useAuth } from "../store/auth";

export default function Reports() {
  const user = useAuth((s) => s.user)!;
  const org = useOrgReport(user.role === "super_admin");
  const trainer = useTrainerReport(user.id, user.role === "trainer");
  const employee = useEmployeeReport(user.id, user.role === "employee");
  const [toast, setToast] = useState<string | null>(null);

  const lmsSync = async () => {
    const r = await integrationsApi.lmsSync();
    setToast(`LMS sync complete — ${r.course_count} courses`);
  };

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Reports</Typography>
        <RoleGuard roles={["super_admin"]}>
          <Button variant="outlined" startIcon={<Sync />} onClick={lmsSync}>Sync LMS</Button>
        </RoleGuard>
      </Stack>

      {org.data && (
        <Stack spacing={2}>
          <Grid container spacing={2}>
            <Grid item xs={6} md={3}><StatCard label="Users" value={org.data.total_users} /></Grid>
            <Grid item xs={6} md={3}><StatCard label="Trainings" value={org.data.total_trainings} color="#0d9488" /></Grid>
            <Grid item xs={6} md={3}><StatCard label="Enrollments" value={org.data.total_enrollments} color="#d97706" /></Grid>
            <Grid item xs={6} md={3}><StatCard label="Pass Rate" value={org.data.assessment_pass_rate} suffix="%" color="#16a34a" /></Grid>
          </Grid>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}><Card variant="outlined"><CardContent><Typography variant="h6">Trainings by Status</Typography><PieSeries data={org.data.trainings_by_status} /></CardContent></Card></Grid>
            <Grid item xs={12} md={6}><Card variant="outlined"><CardContent><Typography variant="h6">Enrollments by Department</Typography><BarSeries data={org.data.enrollments_by_department} /></CardContent></Card></Grid>
          </Grid>
        </Stack>
      )}

      {trainer.data && (
        <Stack spacing={2}>
          <Grid container spacing={2}>
            <Grid item xs={6} md={3}><StatCard label="Trainings" value={trainer.data.trainings_count} /></Grid>
            <Grid item xs={6} md={3}><StatCard label="Sessions" value={trainer.data.sessions_count} color="#0d9488" /></Grid>
            <Grid item xs={6} md={3}><StatCard label="Avg Attendance" value={trainer.data.avg_attendance_rate} suffix="%" color="#d97706" /></Grid>
            <Grid item xs={6} md={3}><StatCard label="Avg Score" value={trainer.data.avg_assessment_score} suffix="%" color="#16a34a" /></Grid>
          </Grid>
          <Card variant="outlined"><CardContent><Typography variant="h6">Enrollments per Training</Typography>
            <BarSeries data={trainer.data.trainings.map((t) => ({ label: t.title, count: t.enrollment_count }))} />
          </CardContent></Card>
        </Stack>
      )}

      {employee.data && (
        <Stack spacing={2}>
          <Grid container spacing={2}>
            <Grid item xs={6} md={3}><StatCard label="Attendance" value={employee.data.attendance_pct} suffix="%" /></Grid>
            <Grid item xs={6} md={3}><StatCard label="Completed" value={employee.data.completed_trainings} color="#16a34a" /></Grid>
            <Grid item xs={6} md={3}><StatCard label="Assessments" value={employee.data.assessments_taken} color="#0d9488" /></Grid>
            <Grid item xs={6} md={3}><StatCard label="Pass Rate" value={employee.data.pass_rate} suffix="%" color="#d97706" /></Grid>
          </Grid>
          <Paper variant="outlined">
            <TableContainer>
              <Table>
                <TableHead><TableRow><TableCell>Assessment</TableCell><TableCell>Score</TableCell><TableCell>Result</TableCell></TableRow></TableHead>
                <TableBody>
                  {employee.data.results.map((r, i) => (
                    <TableRow key={i}><TableCell>{r.assessment_title}</TableCell><TableCell>{r.score}/{r.max_score}</TableCell><TableCell>{r.result}</TableCell></TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Stack>
      )}

      <Snackbar open={!!toast} autoHideDuration={4000} onClose={() => setToast(null)}>
        {toast ? <Alert severity="success">{toast}</Alert> : undefined}
      </Snackbar>
    </Box>
  );
}
