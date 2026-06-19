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
  Paper,
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
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { assessmentsApi } from "../api/resources";
import ConfirmDialog from "../components/ConfirmDialog";
import RoleGuard from "../components/RoleGuard";
import { useAssessments, useMyResults, useTrainings } from "../hooks";
import { useAuth } from "../store/auth";
import type { Assessment } from "../types";

interface NewQ {
  question_text: string;
  question_type: "mcq" | "short";
  options: string;
  correct_answer: string;
}
const emptyQ: NewQ = { question_text: "", question_type: "mcq", options: "", correct_answer: "" };

export default function Assessments() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const user = useAuth((s) => s.user)!;
  const isStaff = user.role === "super_admin" || user.role === "trainer";
  const { data: assessments, isLoading } = useAssessments();
  const { data: myResults } = useMyResults();
  const { data: trainings } = useTrainings({ size: 100 });
  const [toDelete, setToDelete] = useState<Assessment | null>(null);

  // Create-assessment dialog
  const [open, setOpen] = useState(false);
  const [trainingId, setTrainingId] = useState<string>("");
  const [title, setTitle] = useState("");
  const [passing, setPassing] = useState(1);
  const [questions, setQuestions] = useState<NewQ[]>([{ ...emptyQ }]);
  const [busy, setBusy] = useState(false);

  const handleDelete = async (id: number) => {
    await assessmentsApi.remove(id);
    qc.invalidateQueries({ queryKey: ["assessments"] });
  };

  const createAssessment = async () => {
    setBusy(true);
    try {
      await assessmentsApi.create({
        training_id: Number(trainingId),
        title,
        passing_marks: passing,
        questions: questions.map((q, i) => ({
          question_text: q.question_text,
          question_type: q.question_type,
          options: q.question_type === "mcq" ? q.options.split(",").map((o) => o.trim()).filter(Boolean) : null,
          correct_answer: q.correct_answer,
          marks: 1,
          order_index: i,
        })),
      });
      qc.invalidateQueries({ queryKey: ["assessments"] });
      setOpen(false);
      setTrainingId(""); setTitle(""); setPassing(1); setQuestions([{ ...emptyQ }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Assessments</Typography>
        <RoleGuard roles={["super_admin", "trainer"]}>
          <Button variant="contained" startIcon={<Add />} onClick={() => setOpen(true)}>New Assessment</Button>
        </RoleGuard>
      </Stack>

      {isLoading && <Typography>Loading…</Typography>}
      {assessments?.length === 0 && <Typography color="text.secondary">No assessments available.</Typography>}

      <Grid container spacing={2} mb={4}>
        {assessments?.map((a) => (
          <Grid item xs={12} sm={6} md={4} key={a.id}>
            <Card variant="outlined">
              <CardActionArea onClick={() => navigate(`/assessments/${a.id}`)}>
                <CardContent>
                  <Typography variant="h6">{a.title}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ minHeight: 36 }}>
                    {a.description}
                  </Typography>
                  <Stack direction="row" spacing={1} mt={1}>
                    <Chip size="small" label={`${a.question_count} Qs`} />
                    <Chip size="small" label={`${a.duration_minutes} min`} />
                    <Chip size="small" label={`pass ${a.passing_marks}/${a.total_marks}`} />
                  </Stack>
                </CardContent>
              </CardActionArea>
              <RoleGuard roles={["super_admin"]}>
                <CardActions sx={{ justifyContent: "flex-end" }}>
                  <IconButton size="small" color="error" onClick={() => setToDelete(a)}>
                    <Delete fontSize="small" />
                  </IconButton>
                </CardActions>
              </RoleGuard>
            </Card>
          </Grid>
        ))}
      </Grid>

      {user.role === "employee" && (
        <>
          <Typography variant="h6" mb={1}>My Results</Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Assessment #</TableCell>
                  <TableCell>Score</TableCell>
                  <TableCell>Result</TableCell>
                  <TableCell>Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {myResults?.length === 0 && <TableRow><TableCell colSpan={4}>No attempts yet.</TableCell></TableRow>}
                {myResults?.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.assessment_id}</TableCell>
                    <TableCell>{r.score}/{r.max_score}</TableCell>
                    <TableCell>
                      <Chip size="small" label={r.result} color={r.result === "pass" ? "success" : "error"} />
                    </TableCell>
                    <TableCell>{new Date(r.attempt_date).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>New Assessment</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <Stack direction="row" spacing={2}>
              <TextField select label="Course" fullWidth value={trainingId} onChange={(e) => setTrainingId(e.target.value)}>
                {trainings?.items.map((t) => <MenuItem key={t.id} value={String(t.id)}>{t.title}</MenuItem>)}
              </TextField>
              <TextField label="Passing marks" type="number" sx={{ width: 160 }} value={passing} onChange={(e) => setPassing(Number(e.target.value))} />
            </Stack>
            <TextField label="Assessment title" fullWidth value={title} onChange={(e) => setTitle(e.target.value)} />
            {questions.map((q, i) => (
              <Paper key={i} variant="outlined" sx={{ p: 2 }}>
                <Stack spacing={1.5}>
                  <Stack direction="row" spacing={2}>
                    <TextField label={`Question ${i + 1}`} fullWidth value={q.question_text}
                      onChange={(e) => setQuestions((qs) => qs.map((x, j) => j === i ? { ...x, question_text: e.target.value } : x))} />
                    <TextField select label="Type" sx={{ width: 140 }} value={q.question_type}
                      onChange={(e) => setQuestions((qs) => qs.map((x, j) => j === i ? { ...x, question_type: e.target.value as "mcq" | "short" } : x))}>
                      <MenuItem value="mcq">MCQ</MenuItem>
                      <MenuItem value="short">Short</MenuItem>
                    </TextField>
                  </Stack>
                  {q.question_type === "mcq" && (
                    <TextField label="Options (comma-separated)" fullWidth value={q.options}
                      onChange={(e) => setQuestions((qs) => qs.map((x, j) => j === i ? { ...x, options: e.target.value } : x))} />
                  )}
                  <TextField label="Correct answer" fullWidth value={q.correct_answer}
                    onChange={(e) => setQuestions((qs) => qs.map((x, j) => j === i ? { ...x, correct_answer: e.target.value } : x))} />
                </Stack>
              </Paper>
            ))}
            <Button startIcon={<Add />} onClick={() => setQuestions((qs) => [...qs, { ...emptyQ }])}>Add question</Button>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained"
            disabled={busy || !trainingId || !title || questions.some((q) => !q.question_text || !q.correct_answer)}
            onClick={createAssessment}>
            {busy ? "Saving…" : "Create"}
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmDialog
        open={!!toDelete}
        title="Delete quiz"
        message={`Delete "${toDelete?.title}"? Its questions and all attempt results will be removed. This cannot be undone.`}
        confirmText="Delete"
        onClose={() => setToDelete(null)}
        onConfirm={() => toDelete && handleDelete(toDelete.id)}
      />
    </Box>
  );
}
