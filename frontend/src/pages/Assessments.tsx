import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Grid,
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
import { useNavigate } from "react-router-dom";

import { useAssessments, useMyResults } from "../hooks";
import { useAuth } from "../store/auth";

export default function Assessments() {
  const navigate = useNavigate();
  const user = useAuth((s) => s.user)!;
  const { data: assessments, isLoading } = useAssessments();
  const { data: myResults } = useMyResults();

  return (
    <Box>
      <Typography variant="h4" mb={2}>Assessments</Typography>

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
    </Box>
  );
}
