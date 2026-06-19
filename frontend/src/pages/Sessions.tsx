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

import { useSessions } from "../hooks";

export default function Sessions() {
  const { data: sessions, isLoading } = useSessions();

  return (
    <Box>
      <Typography variant="h4" mb={2}>Sessions</Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Mode</TableCell>
              <TableCell>Location</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && <TableRow><TableCell colSpan={4}>Loading…</TableCell></TableRow>}
            {sessions?.length === 0 && <TableRow><TableCell colSpan={4}>No sessions scheduled.</TableCell></TableRow>}
            {sessions?.map((s) => (
              <TableRow key={s.id} hover>
                <TableCell>{s.title}</TableCell>
                <TableCell>{s.session_date}</TableCell>
                <TableCell><Chip size="small" label={s.mode} /></TableCell>
                <TableCell>{s.location ?? "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
