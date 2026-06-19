import { Send } from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  Snackbar,
  Stack,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { enrollmentRequestsApi } from "../api/resources";

export default function BrowseCourses() {
  const qc = useQueryClient();
  const { data: courses, isLoading } = useQuery({
    queryKey: ["available-courses"],
    queryFn: enrollmentRequestsApi.available,
  });
  const [toast, setToast] = useState<string | null>(null);
  const request = useMutation({
    mutationFn: enrollmentRequestsApi.create,
    onSuccess: () => {
      setToast("Request sent — a trainer or admin will review it.");
      qc.invalidateQueries({ queryKey: ["available-courses"] });
    },
    onError: (e: any) => setToast(e?.response?.data?.detail ?? "Could not send request"),
  });

  return (
    <Box>
      <Typography variant="h4" mb={1}>Browse Courses</Typography>
      <Typography variant="body2" color="text.secondary" mb={2}>
        Courses you're not part of yet. Request to join — once a trainer or admin approves, you're enrolled.
      </Typography>

      {isLoading && <Typography>Loading…</Typography>}
      {courses?.length === 0 && <Typography color="text.secondary">You're enrolled in (or have requested) every available course.</Typography>}

      <Grid container spacing={2}>
        {courses?.map((c) => (
          <Grid item xs={12} sm={6} md={4} key={c.id}>
            <Card variant="outlined" sx={{ height: "100%" }}>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" mb={1}>
                  <Chip size="small" label={c.status} />
                  {c.category && <Typography variant="caption" color="text.secondary">{c.category}</Typography>}
                </Stack>
                <Typography variant="h6">{c.title}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ minHeight: 40 }}>
                  {c.description?.slice(0, 90) || "No description"}
                </Typography>
                <Button
                  fullWidth variant="contained" startIcon={<Send />} sx={{ mt: 1 }}
                  disabled={request.isPending}
                  onClick={() => request.mutate(c.id)}
                >
                  Request to join
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Snackbar open={!!toast} autoHideDuration={4000} onClose={() => setToast(null)}>
        {toast ? <Alert severity="info" onClose={() => setToast(null)}>{toast}</Alert> : undefined}
      </Snackbar>
    </Box>
  );
}
