import { Add, AutoAwesome, Delete, QrCode2 } from "@mui/icons-material";
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Paper,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";

import RoleGuard from "../components/RoleGuard";
import SessionQrDialog from "../components/SessionQrDialog";
import { type QrToken, aiApi, qrApi, sessionsApi } from "../api/resources";
import {
  useAssessments,
  useEnrollments,
  useSessionMutations,
  useSessions,
  useTraining,
  useTrainingMutations,
  useUsers,
} from "../hooks";
import { useQueryClient } from "@tanstack/react-query";

export default function TrainingDetail() {
  const { id } = useParams();
  const trainingId = Number(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [tab, setTab] = useState(0);
  const { data: training } = useTraining(trainingId);

  if (!training) return <Typography>Loading…</Typography>;

  return (
    <Box>
      <Button onClick={() => navigate("/trainings")} sx={{ mb: 1 }}>← Back</Button>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="h4">{training.title}</Typography>
        <Chip label={training.status} color="primary" />
      </Stack>
      <Typography color="text.secondary" mb={2}>{training.description}</Typography>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Overview" />
        <Tab label="Enrollments" />
        <Tab label="Sessions" />
        <Tab label="Assessments" />
      </Tabs>

      {tab === 0 && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Grid container spacing={2}>
            {[
              ["Category", training.category ?? "—"],
              ["Capacity", training.capacity ?? "—"],
              ["Start", training.start_date ?? "—"],
              ["End", training.end_date ?? "—"],
            ].map(([k, v]) => (
              <Grid item xs={6} md={3} key={k}>
                <Typography variant="caption" color="text.secondary">{k}</Typography>
                <Typography>{String(v)}</Typography>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {tab === 1 && <EnrollmentsTab trainingId={trainingId} />}
      {tab === 2 && <SessionsTab trainingId={trainingId} />}
      {tab === 3 && (
        <AssessmentsTab
          trainingId={trainingId}
          onGenerated={() => qc.invalidateQueries({ queryKey: ["assessments", trainingId] })}
        />
      )}
    </Box>
  );
}

function EnrollmentsTab({ trainingId }: { trainingId: number }) {
  const { data: enrollments } = useEnrollments(trainingId);
  const { data: users } = useUsers({ role: "employee", size: 100 });
  const { enroll, unenroll } = useTrainingMutations();
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<number[]>([]);

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <RoleGuard roles={["super_admin", "trainer"]}>
        <Button startIcon={<Add />} variant="contained" sx={{ mb: 2 }} onClick={() => { setSelected([]); setOpen(true); }}>
          Enroll users
        </Button>
      </RoleGuard>
      <List dense>
        {enrollments?.length === 0 && <Typography color="text.secondary">No enrollments yet.</Typography>}
        {enrollments?.map((e) => (
          <ListItem
            key={e.id}
            secondaryAction={
              <RoleGuard roles={["super_admin", "trainer"]}>
                <IconButton edge="end" color="error" onClick={() => unenroll.mutate({ id: trainingId, userId: e.user_id })}>
                  <Delete fontSize="small" />
                </IconButton>
              </RoleGuard>
            }
          >
            <ListItemText
              primary={e.user ? `${e.user.name} (${e.user.employee_code})` : `User #${e.user_id}`}
              secondary={`Status: ${e.status}`}
            />
          </ListItem>
        ))}
      </List>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Enroll users</DialogTitle>
        <DialogContent>
          <TextField
            select
            SelectProps={{ multiple: true }}
            fullWidth
            label="Employees"
            value={selected}
            onChange={(e) => setSelected((e.target.value as unknown as number[]).map(Number))}
            sx={{ mt: 1 }}
          >
            {users?.items.map((u) => (
              <MenuItem key={u.id} value={u.id}>{u.name} ({u.email})</MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            disabled={!selected.length}
            onClick={() => { enroll.mutate({ id: trainingId, userIds: selected }); setOpen(false); }}
          >
            Enroll {selected.length || ""}
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
}

interface SForm {
  title: string;
  session_date: string;
  start_time: string;
  end_time: string;
  location: string;
  mode: string;
  meeting_link: string;
}

function SessionsTab({ trainingId }: { trainingId: number }) {
  const qc = useQueryClient();
  const { data: sessions } = useSessions(trainingId);
  const { create } = useSessionMutations();
  const [open, setOpen] = useState(false);
  const { register, handleSubmit, reset } = useForm<SForm>();

  // QR state
  const [qrToken, setQrToken] = useState<QrToken | null>(null);
  const [qrSession, setQrSession] = useState<{ id: number; title: string } | null>(null);

  const onSubmit = (form: SForm) => {
    create.mutate({
      training_id: trainingId,
      title: form.title,
      session_date: form.session_date,
      start_time: form.start_time || null,
      end_time: form.end_time || null,
      location: form.location || null,
      mode: form.mode || "offline",
      meeting_link: form.meeting_link || null,
    });
    setOpen(false);
  };

  const endAndGenerate = async (s: { id: number; title: string }) => {
    await sessionsApi.end(s.id);
    const token = await qrApi.generate(s.id);
    qc.invalidateQueries({ queryKey: ["sessions"] });
    setQrSession(s);
    setQrToken(token);
  };

  const regenerate = async () => {
    if (qrSession) setQrToken(await qrApi.generate(qrSession.id));
  };
  const revoke = async () => {
    if (qrSession) await qrApi.revoke(qrSession.id);
    setQrToken(null);
    setQrSession(null);
  };

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <RoleGuard roles={["super_admin", "trainer"]}>
        <Button startIcon={<Add />} variant="contained" sx={{ mb: 2 }}
          onClick={() => { reset({ title: "", session_date: "", start_time: "", end_time: "", location: "", mode: "offline", meeting_link: "" }); setOpen(true); }}>
          Add session
        </Button>
      </RoleGuard>
      <List dense>
        {sessions?.length === 0 && <Typography color="text.secondary">No sessions yet.</Typography>}
        {sessions?.map((s) => (
          <ListItem
            key={s.id}
            secondaryAction={
              <RoleGuard roles={["super_admin", "trainer"]}>
                <Button size="small" variant="outlined" startIcon={<QrCode2 />} onClick={() => endAndGenerate({ id: s.id, title: s.title })}>
                  {s.status === "ended" ? "Show QR" : "End & QR"}
                </Button>
              </RoleGuard>
            }
          >
            <ListItemText
              primary={
                <span>
                  {s.title} — {s.session_date}{" "}
                  <Chip size="small" label={s.status} color={s.status === "ended" ? "default" : "success"} sx={{ ml: 1 }} />
                </span>
              }
              secondary={`${s.mode} · ${s.location ?? "—"}`}
            />
          </ListItem>
        ))}
      </List>

      <SessionQrDialog
        token={qrToken}
        sessionTitle={qrSession?.title ?? ""}
        onRegenerate={regenerate}
        onRevoke={revoke}
        onClose={() => { setQrToken(null); setQrSession(null); }}
      />

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Add session</DialogTitle>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogContent>
            <Stack spacing={2} mt={1}>
              <TextField label="Title" fullWidth {...register("title")} />
              <TextField label="Date" type="date" InputLabelProps={{ shrink: true }} fullWidth {...register("session_date")} />
              <Stack direction="row" spacing={2}>
                <TextField label="Start" type="time" InputLabelProps={{ shrink: true }} fullWidth {...register("start_time")} />
                <TextField label="End" type="time" InputLabelProps={{ shrink: true }} fullWidth {...register("end_time")} />
              </Stack>
              <TextField label="Location" fullWidth {...register("location")} />
              <TextField select label="Mode" defaultValue="offline" fullWidth {...register("mode")}>
                <MenuItem value="offline">Offline</MenuItem>
                <MenuItem value="online">Online</MenuItem>
                <MenuItem value="hybrid">Hybrid</MenuItem>
              </TextField>
              <TextField label="Meeting link" fullWidth {...register("meeting_link")} />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained">Create</Button>
          </DialogActions>
        </form>
      </Dialog>
    </Paper>
  );
}

function AssessmentsTab({ trainingId, onGenerated }: { trainingId: number; onGenerated: () => void }) {
  const navigate = useNavigate();
  const { data: assessments } = useAssessments(trainingId);
  const [open, setOpen] = useState(false);
  const [material, setMaterial] = useState("");
  const [num, setNum] = useState(5);
  const [busy, setBusy] = useState(false);

  const generate = async () => {
    setBusy(true);
    try {
      await aiApi.generateAssessment({ training_id: trainingId, material_text: material, num_questions: num, types: ["mcq", "short"] });
      onGenerated();
      setOpen(false);
      setMaterial("");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <RoleGuard roles={["super_admin", "trainer"]}>
        <Button startIcon={<AutoAwesome />} variant="contained" sx={{ mb: 2 }} onClick={() => setOpen(true)}>
          Generate AI assessment
        </Button>
      </RoleGuard>
      <List dense>
        {assessments?.length === 0 && <Typography color="text.secondary">No assessments yet.</Typography>}
        {assessments?.map((a) => (
          <ListItem key={a.id} button onClick={() => navigate(`/assessments/${a.id}`)}>
            <ListItemText primary={a.title} secondary={`${a.question_count} questions · pass ${a.passing_marks}/${a.total_marks}`} />
          </ListItem>
        ))}
      </List>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Generate AI assessment</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField label="Material text" fullWidth multiline rows={5} value={material} onChange={(e) => setMaterial(e.target.value)} />
            <TextField label="Number of questions" type="number" value={num} onChange={(e) => setNum(Number(e.target.value))} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" disabled={busy || !material} onClick={generate}>
            {busy ? "Generating…" : "Generate"}
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
}
