import {
  Box,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import { useMyAttendance } from "../hooks";
import type { AttendanceStatus } from "../types";

const COLOR: Record<AttendanceStatus, "success" | "error" | "warning" | "default"> = {
  present: "success",
  absent: "error",
  late: "warning",
  excused: "default",
};

export default function AttendanceMine() {
  const { data, isLoading } = useMyAttendance();

  return (
    <Box>
      <Typography variant="h4" mb={2}>My Attendance</Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Training</TableCell>
              <TableCell>Session</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && <TableRow><TableCell colSpan={4}>Loading…</TableCell></TableRow>}
            {data?.length === 0 && <TableRow><TableCell colSpan={4}>No attendance records yet.</TableCell></TableRow>}
            {data?.map((a) => (
              <TableRow key={a.id} hover>
                <TableCell>{a.training_title}</TableCell>
                <TableCell>{a.session_title}</TableCell>
                <TableCell>{a.session_date}</TableCell>
                <TableCell><Chip size="small" label={a.status} color={COLOR[a.status]} /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
