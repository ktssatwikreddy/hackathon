import {
  Alert,
  Box,
  Button,
  MenuItem,
  Paper,
  Snackbar,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";

import { type AttendanceEntry } from "../api/resources";
import { useEnrollments, useMarkAttendance, useSessions, useTrainings } from "../hooks";
import type { AttendanceStatus } from "../types";

const STATUSES: AttendanceStatus[] = ["present", "absent", "late", "excused"];

export default function AttendanceMark() {
  const [trainingId, setTrainingId] = useState<number | "">("");
  const [sessionId, setSessionId] = useState<number | "">("");
  const [marks, setMarks] = useState<Record<number, AttendanceStatus>>({});
  const [toast, setToast] = useState<{ msg: string; sev: "success" | "error" } | null>(null);

  const { data: trainings } = useTrainings({ size: 100 });
  const { data: sessions } = useSessions(trainingId || undefined);
  const { data: enrollments } = useEnrollments(trainingId || 0);
  const mark = useMarkAttendance();

  const submit = () => {
    if (!sessionId) return;
    const entries: AttendanceEntry[] = (enrollments ?? []).map((e) => ({
      user_id: e.user_id,
      status: marks[e.user_id] ?? "present",
    }));
    mark.mutate(
      { sessionId: Number(sessionId), entries },
      {
        onSuccess: () => setToast({ msg: "Attendance recorded", sev: "success" }),
        onError: (err: any) =>
          setToast({ msg: err?.response?.data?.detail ?? "Failed to record (already marked?)", sev: "error" }),
      }
    );
  };

  return (
    <Box>
      <Typography variant="h4" mb={2}>Mark Attendance</Typography>
      <Stack direction="row" spacing={2} mb={2}>
        <TextField
          select size="small" label="Training" sx={{ width: 260 }}
          value={trainingId}
          onChange={(e) => { setTrainingId(Number(e.target.value)); setSessionId(""); }}
        >
          {trainings?.items.map((t) => <MenuItem key={t.id} value={t.id}>{t.title}</MenuItem>)}
        </TextField>
        <TextField
          select size="small" label="Session" sx={{ width: 260 }}
          value={sessionId}
          disabled={!trainingId}
          onChange={(e) => setSessionId(Number(e.target.value))}
        >
          {sessions?.map((s) => <MenuItem key={s.id} value={s.id}>{s.title} ({s.session_date})</MenuItem>)}
        </TextField>
      </Stack>

      {trainingId && enrollments?.length === 0 && (
        <Alert severity="info">No enrolled users in this training.</Alert>
      )}

      {sessionId && enrollments && enrollments.length > 0 && (
        <Paper variant="outlined">
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell width={200}>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {enrollments.map((e) => (
                  <TableRow key={e.user_id}>
                    <TableCell>{e.user ? `${e.user.name} (${e.user.employee_code})` : `User #${e.user_id}`}</TableCell>
                    <TableCell>
                      <TextField
                        select size="small" fullWidth
                        value={marks[e.user_id] ?? "present"}
                        onChange={(ev) => setMarks((m) => ({ ...m, [e.user_id]: ev.target.value as AttendanceStatus }))}
                      >
                        {STATUSES.map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
                      </TextField>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <Box sx={{ p: 2 }}>
            <Button variant="contained" onClick={submit} disabled={mark.isPending}>
              Submit attendance
            </Button>
          </Box>
        </Paper>
      )}

      <Snackbar open={!!toast} autoHideDuration={4000} onClose={() => setToast(null)}>
        {toast ? <Alert severity={toast.sev}>{toast.msg}</Alert> : undefined}
      </Snackbar>
    </Box>
  );
}
