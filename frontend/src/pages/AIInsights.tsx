import { AutoAwesome, CheckCircle, TipsAndUpdates, TrendingDown } from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";

import { aiApi } from "../api/resources";
import StatCard from "../components/StatCard";
import { useUsers } from "../hooks";
import { useAuth } from "../store/auth";
import type { PerformanceInsight } from "../types";

export default function AIInsights() {
  const user = useAuth((s) => s.user)!;
  const isStaff = user.role === "super_admin" || user.role === "trainer";
  const { data: users } = useUsers({ role: "employee", size: 100 });
  const [target, setTarget] = useState<number>(user.id);
  const [insight, setInsight] = useState<PerformanceInsight | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      setInsight(await aiApi.analyzePerformance(isStaff ? target : user.id));
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" mb={1}>AI Performance Insights</Typography>
      <Typography color="text.secondary" mb={2}>
        Generates a summary, learning gaps, and recommendations from attendance and assessment data.
      </Typography>

      <Stack direction="row" spacing={2} mb={3} alignItems="center">
        {isStaff && (
          <TextField select size="small" label="Employee" sx={{ width: 280 }} value={target} onChange={(e) => setTarget(Number(e.target.value))}>
            {users?.items.map((u) => <MenuItem key={u.id} value={u.id}>{u.name} ({u.email})</MenuItem>)}
          </TextField>
        )}
        <Button variant="contained" startIcon={<AutoAwesome />} onClick={run} disabled={loading}>
          {loading ? "Analyzing…" : "Analyze performance"}
        </Button>
      </Stack>

      {loading && <Box sx={{ display: "grid", placeItems: "center", height: 200 }}><CircularProgress /></Box>}
      {error && <Alert severity="error">{error}</Alert>}

      {insight && !loading && (
        <Stack spacing={2}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}><StatCard label="Attendance" value={insight.attendance_pct} suffix="%" /></Grid>
            <Grid item xs={12} sm={4}><StatCard label="Avg Score" value={insight.avg_score} suffix="%" color="#0d9488" /></Grid>
            <Grid item xs={12} sm={4}><StatCard label="Completed Trainings" value={insight.completed_trainings} color="#16a34a" /></Grid>
          </Grid>

          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>Summary</Typography>
              <Typography>{insight.summary}</Typography>
            </CardContent>
          </Card>

          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Card variant="outlined" sx={{ height: "100%" }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom><TrendingDown sx={{ verticalAlign: "middle", mr: 1, color: "error.main" }} />Learning Gaps</Typography>
                  <List dense>
                    {insight.learning_gaps.map((g, i) => (
                      <ListItem key={i}><ListItemText primary={g} /></ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined" sx={{ height: "100%" }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom><CheckCircle sx={{ verticalAlign: "middle", mr: 1, color: "success.main" }} />Skill Areas</Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                    {insight.skill_areas.map((s, i) => <Chip key={i} label={s} />)}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined" sx={{ height: "100%" }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom><TipsAndUpdates sx={{ verticalAlign: "middle", mr: 1, color: "warning.main" }} />Recommendations</Typography>
                  <List dense>
                    {insight.recommendations.map((r, i) => (
                      <ListItem key={i}><ListItemIcon sx={{ minWidth: 28 }}>•</ListItemIcon><ListItemText primary={r} /></ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Stack>
      )}
    </Box>
  );
}
