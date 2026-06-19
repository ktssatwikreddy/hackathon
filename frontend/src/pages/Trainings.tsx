import { Add, Delete } from "@mui/icons-material";
import {
  Box,
  Button,
  Card,
  CardActionArea,
  CardActions,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import ConfirmDialog from "../components/ConfirmDialog";
import RoleGuard from "../components/RoleGuard";
import { useDepartments, useTrainingMutations, useTrainings } from "../hooks";
import type { Training, TrainingStatus } from "../types";

const STATUS_COLOR: Record<TrainingStatus, "default" | "info" | "success" | "warning" | "error"> = {
  draft: "default",
  scheduled: "info",
  active: "success",
  completed: "default",
  cancelled: "error",
};

interface TForm {
  title: string;
  description: string;
  category: string;
  department_id: string;
  status: TrainingStatus;
}

export default function Trainings() {
  const navigate = useNavigate();
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const { data, isLoading } = useTrainings({ status: status || undefined, search: search || undefined, size: 50 });
  const { data: departments } = useDepartments();
  const { create, remove } = useTrainingMutations();
  const [open, setOpen] = useState(false);
  const [toDelete, setToDelete] = useState<Training | null>(null);
  const { register, handleSubmit, reset } = useForm<TForm>();

  const onSubmit = (form: TForm) => {
    create.mutate({
      title: form.title,
      description: form.description || null,
      category: form.category || null,
      department_id: form.department_id ? Number(form.department_id) : null,
      status: form.status,
    });
    setOpen(false);
  };

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Trainings</Typography>
        <RoleGuard roles={["super_admin", "trainer"]}>
          <Button variant="contained" startIcon={<Add />} onClick={() => { reset({ title: "", description: "", category: "", department_id: "", status: "draft" }); setOpen(true); }}>
            New Training
          </Button>
        </RoleGuard>
      </Stack>

      <Stack direction="row" spacing={2} mb={2}>
        <TextField size="small" label="Search" value={search} onChange={(e) => setSearch(e.target.value)} />
        <TextField size="small" select label="Status" value={status} onChange={(e) => setStatus(e.target.value)} sx={{ width: 180 }}>
          <MenuItem value="">All</MenuItem>
          {["draft", "scheduled", "active", "completed", "cancelled"].map((s) => (
            <MenuItem key={s} value={s}>{s}</MenuItem>
          ))}
        </TextField>
      </Stack>

      {isLoading && <Typography>Loading…</Typography>}
      {data?.items.length === 0 && <Typography color="text.secondary">No trainings found.</Typography>}

      <Grid container spacing={2}>
        {data?.items.map((t) => (
          <Grid item xs={12} sm={6} md={4} key={t.id}>
            <Card variant="outlined">
              <CardActionArea onClick={() => navigate(`/trainings/${t.id}`)}>
                <CardContent>
                  <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
                    <Chip size="small" label={t.status} color={STATUS_COLOR[t.status]} />
                    {t.category && <Typography variant="caption" color="text.secondary">{t.category}</Typography>}
                  </Stack>
                  <Typography variant="h6">{t.title}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ minHeight: 40 }}>
                    {t.description?.slice(0, 90) || "No description"}
                  </Typography>
                </CardContent>
              </CardActionArea>
              <RoleGuard roles={["super_admin"]}>
                <CardActions sx={{ justifyContent: "flex-end" }}>
                  <IconButton size="small" color="error" onClick={() => setToDelete(t)}>
                    <Delete fontSize="small" />
                  </IconButton>
                </CardActions>
              </RoleGuard>
            </Card>
          </Grid>
        ))}
      </Grid>

      <ConfirmDialog
        open={!!toDelete}
        title="Delete course"
        message={`Delete "${toDelete?.title}"? This removes its sessions, enrollments, attendance and assessments. This cannot be undone.`}
        confirmText="Delete"
        onClose={() => setToDelete(null)}
        onConfirm={() => toDelete && remove.mutate(toDelete.id)}
      />

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>New Training</DialogTitle>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogContent>
            <Stack spacing={2} mt={1}>
              <TextField label="Title" fullWidth {...register("title")} />
              <TextField label="Description" fullWidth multiline rows={3} {...register("description")} />
              <TextField label="Category" fullWidth {...register("category")} />
              <TextField select label="Department" fullWidth defaultValue="" {...register("department_id")}>
                <MenuItem value="">Open to all</MenuItem>
                {departments?.map((d) => <MenuItem key={d.id} value={String(d.id)}>{d.name}</MenuItem>)}
              </TextField>
              <TextField select label="Status" fullWidth defaultValue="draft" {...register("status")}>
                {["draft", "scheduled", "active", "completed", "cancelled"].map((s) => (
                  <MenuItem key={s} value={s}>{s}</MenuItem>
                ))}
              </TextField>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained">Create</Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}
