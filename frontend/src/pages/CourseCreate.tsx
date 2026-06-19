import { Add, Delete } from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  IconButton,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useFieldArray, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { coursesApi } from "../api/resources";
import { useDepartments, useUsers } from "../hooks";

interface SessionRow {
  title: string;
  session_date: string;
  start_time: string;
  end_time: string;
  location: string;
  mode: string;
}

interface CourseForm {
  title: string;
  description: string;
  category: string;
  department_id: string;
  trainer_id: string;
  sessions: SessionRow[];
}

const emptySession: SessionRow = {
  title: "",
  session_date: "",
  start_time: "",
  end_time: "",
  location: "",
  mode: "offline",
};

export default function CourseCreate() {
  const navigate = useNavigate();
  const { data: trainers } = useUsers({ role: "trainer", size: 100 });
  const { data: departments } = useDepartments();
  const [error, setError] = useState<string | null>(null);

  const { register, control, handleSubmit, formState: { isSubmitting } } = useForm<CourseForm>({
    defaultValues: {
      title: "",
      description: "",
      category: "",
      department_id: "",
      trainer_id: "",
      sessions: [{ ...emptySession }],
    },
  });
  const { fields, append, remove } = useFieldArray({ control, name: "sessions" });

  const onSubmit = async (form: CourseForm) => {
    setError(null);
    try {
      await coursesApi.create({
        title: form.title,
        description: form.description || null,
        category: form.category || null,
        department_id: form.department_id ? Number(form.department_id) : null,
        trainer_id: Number(form.trainer_id),
        total_sessions: form.sessions.length,
        sessions: form.sessions.map((s) => ({
          title: s.title,
          session_date: s.session_date,
          start_time: s.start_time || null,
          end_time: s.end_time || null,
          location: s.location || null,
          mode: s.mode,
        })),
      });
      navigate("/trainings");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Failed to create course");
    }
  };

  return (
    <Box>
      <Typography variant="h4" mb={2}>Create Course</Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{String(error)}</Alert>}

      <form onSubmit={handleSubmit(onSubmit)}>
        <Card variant="outlined" sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" mb={2}>Course details</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}><TextField label="Title" fullWidth required {...register("title")} /></Grid>
              <Grid item xs={12} md={6}><TextField label="Category" fullWidth {...register("category")} /></Grid>
              <Grid item xs={12}><TextField label="Description" fullWidth multiline rows={2} {...register("description")} /></Grid>
              <Grid item xs={12} md={6}>
                <TextField select label="Trainer" fullWidth required defaultValue="" {...register("trainer_id")}>
                  {trainers?.items.map((t) => <MenuItem key={t.id} value={String(t.id)}>{t.name} ({t.email})</MenuItem>)}
                </TextField>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField select label="Department" fullWidth defaultValue="" {...register("department_id")}>
                  <MenuItem value="">Open to all</MenuItem>
                  {departments?.map((d) => <MenuItem key={d.id} value={String(d.id)}>{d.name}</MenuItem>)}
                </TextField>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
          <Typography variant="h6">Schedule ({fields.length} session{fields.length !== 1 ? "s" : ""})</Typography>
          <Button startIcon={<Add />} onClick={() => append({ ...emptySession })}>Add session</Button>
        </Stack>

        <Stack spacing={2} mb={3}>
          {fields.map((field, i) => (
            <Paper key={field.id} variant="outlined" sx={{ p: 2 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} md={3}><TextField label={`Session ${i + 1} title`} fullWidth required {...register(`sessions.${i}.title`)} /></Grid>
                <Grid item xs={6} md={2}><TextField type="date" label="Date" InputLabelProps={{ shrink: true }} fullWidth required {...register(`sessions.${i}.session_date`)} /></Grid>
                <Grid item xs={6} md={2}><TextField type="time" label="Start" InputLabelProps={{ shrink: true }} fullWidth {...register(`sessions.${i}.start_time`)} /></Grid>
                <Grid item xs={6} md={2}><TextField type="time" label="End" InputLabelProps={{ shrink: true }} fullWidth {...register(`sessions.${i}.end_time`)} /></Grid>
                <Grid item xs={6} md={2}>
                  <TextField select label="Mode" fullWidth defaultValue="offline" {...register(`sessions.${i}.mode`)}>
                    <MenuItem value="offline">Offline</MenuItem>
                    <MenuItem value="online">Online</MenuItem>
                    <MenuItem value="hybrid">Hybrid</MenuItem>
                  </TextField>
                </Grid>
                <Grid item xs={12} md={1}>
                  <IconButton color="error" disabled={fields.length === 1} onClick={() => remove(i)}><Delete /></IconButton>
                </Grid>
                <Grid item xs={12}><TextField label="Location / meeting link" fullWidth {...register(`sessions.${i}.location`)} /></Grid>
              </Grid>
            </Paper>
          ))}
        </Stack>

        <Stack direction="row" spacing={2}>
          <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
            {isSubmitting ? "Creating…" : "Create course"}
          </Button>
          <Button onClick={() => navigate("/trainings")}>Cancel</Button>
        </Stack>
      </form>
    </Box>
  );
}
