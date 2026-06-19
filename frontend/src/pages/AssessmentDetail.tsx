import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  FormControl,
  FormControlLabel,
  Paper,
  Radio,
  RadioGroup,
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
import { useNavigate, useParams } from "react-router-dom";

import { assessmentsApi } from "../api/resources";
import { useAuth } from "../store/auth";
import type { AssessmentResult } from "../types";

export default function AssessmentDetail() {
  const { id } = useParams();
  const assessmentId = Number(id);
  const navigate = useNavigate();
  const user = useAuth((s) => s.user)!;
  const isStaff = user.role === "super_admin" || user.role === "trainer";

  const { data: assessment } = useQuery({
    queryKey: ["assessment", assessmentId],
    queryFn: () => assessmentsApi.get(assessmentId),
  });
  const { data: questions } = useQuery({
    queryKey: ["assessment", assessmentId, "questions"],
    queryFn: () => assessmentsApi.questions(assessmentId),
  });
  const { data: results } = useQuery({
    queryKey: ["assessment", assessmentId, "results"],
    queryFn: () => assessmentsApi.results(assessmentId),
    enabled: isStaff,
  });

  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!assessment) return <Typography>Loading…</Typography>;

  const submit = async () => {
    setError(null);
    try {
      const r = await assessmentsApi.submit(assessmentId, answers);
      setResult(r);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Submission failed");
    }
  };

  return (
    <Box>
      <Button onClick={() => navigate("/assessments")} sx={{ mb: 1 }}>← Back</Button>
      <Typography variant="h4">{assessment.title}</Typography>
      <Typography color="text.secondary" mb={2}>
        {assessment.description} · pass {assessment.passing_marks}/{assessment.total_marks} · {assessment.duration_minutes} min
      </Typography>

      {result && (
        <Alert severity={result.result === "pass" ? "success" : "warning"} sx={{ mb: 2 }}>
          You scored {result.score}/{result.max_score} — <strong>{result.result.toUpperCase()}</strong>
        </Alert>
      )}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Staff: results table. Employees: take the assessment. */}
      {isStaff ? (
        <Paper variant="outlined">
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell>Score</TableCell>
                  <TableCell>Result</TableCell>
                  <TableCell>Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {results?.length === 0 && <TableRow><TableCell colSpan={4}>No attempts yet.</TableCell></TableRow>}
                {results?.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>#{r.user_id}</TableCell>
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
        </Paper>
      ) : (
        <Stack spacing={2}>
          {questions?.map((q, i) => (
            <Card key={q.id} variant="outlined">
              <CardContent>
                <Typography fontWeight={600} mb={1}>
                  {i + 1}. {q.question_text} <Chip size="small" label={`${q.marks} mark`} sx={{ ml: 1 }} />
                </Typography>
                {q.question_type === "mcq" && q.options ? (
                  <FormControl>
                    <RadioGroup
                      value={answers[q.id] ?? ""}
                      onChange={(e) => setAnswers((a) => ({ ...a, [q.id]: e.target.value }))}
                    >
                      {q.options.map((opt) => (
                        <FormControlLabel key={opt} value={opt} control={<Radio />} label={opt} />
                      ))}
                    </RadioGroup>
                  </FormControl>
                ) : (
                  <TextField
                    fullWidth multiline={q.question_type !== "short"}
                    rows={q.question_type === "short" ? 1 : 4}
                    placeholder="Your answer"
                    value={answers[q.id] ?? ""}
                    onChange={(e) => setAnswers((a) => ({ ...a, [q.id]: e.target.value }))}
                  />
                )}
              </CardContent>
            </Card>
          ))}
          <Box>
            <Button variant="contained" size="large" onClick={submit} disabled={!!result}>
              Submit answers
            </Button>
          </Box>
        </Stack>
      )}
    </Box>
  );
}
