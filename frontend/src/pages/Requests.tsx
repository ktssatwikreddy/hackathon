import { Check, Close } from "@mui/icons-material";
import {
  Box,
  Button,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { enrollmentRequestsApi } from "../api/resources";

export default function Requests() {
  const qc = useQueryClient();
  const { data: requests, isLoading } = useQuery({
    queryKey: ["enrollment-requests"],
    queryFn: enrollmentRequestsApi.list,
  });
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["enrollment-requests"] });
    qc.invalidateQueries({ queryKey: ["notifications"] });
  };
  const approve = useMutation({ mutationFn: enrollmentRequestsApi.approve, onSuccess: invalidate });
  const reject = useMutation({ mutationFn: enrollmentRequestsApi.reject, onSuccess: invalidate });

  return (
    <Box>
      <Typography variant="h4" mb={2}>Enrollment Requests</Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Employee</TableCell>
              <TableCell>Course</TableCell>
              <TableCell>Requested</TableCell>
              <TableCell align="right">Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && <TableRow><TableCell colSpan={4}>Loading…</TableCell></TableRow>}
            {requests?.length === 0 && <TableRow><TableCell colSpan={4}>No pending requests.</TableCell></TableRow>}
            {requests?.map((r) => (
              <TableRow key={r.id} hover>
                <TableCell>{r.user_name}</TableCell>
                <TableCell>{r.training_title}</TableCell>
                <TableCell>{new Date(r.created_at).toLocaleString()}</TableCell>
                <TableCell align="right">
                  <Stack direction="row" spacing={1} justifyContent="flex-end">
                    <Button size="small" variant="contained" color="success" startIcon={<Check />}
                      disabled={approve.isPending} onClick={() => approve.mutate(r.id)}>
                      Approve
                    </Button>
                    <Button size="small" variant="outlined" color="error" startIcon={<Close />}
                      disabled={reject.isPending} onClick={() => reject.mutate(r.id)}>
                      Reject
                    </Button>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
