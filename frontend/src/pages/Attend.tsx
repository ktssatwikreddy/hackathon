import { CheckCircle, ErrorOutline, HourglassEmpty } from "@mui/icons-material";
import { Box, Button, Card, CardContent, CircularProgress, Stack, Typography } from "@mui/material";
import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { attendanceApi } from "../api/resources";
import { useAuth } from "../store/auth";

type State =
  | { kind: "loading" }
  | { kind: "success"; training: string; already: boolean }
  | { kind: "error"; message: string };

export default function Attend() {
  const { token = "" } = useParams();
  const navigate = useNavigate();
  const user = useAuth((s) => s.user);
  const accessToken = useAuth((s) => s.accessToken);
  const [state, setState] = useState<State>({ kind: "loading" });
  const ran = useRef(false);

  useEffect(() => {
    // Not logged in → bounce to login, return here afterwards.
    if (!accessToken || !user) {
      navigate(`/login?next=${encodeURIComponent(`/attend/${token}`)}`, { replace: true });
      return;
    }
    if (ran.current) return;
    ran.current = true;
    attendanceApi
      .checkin(token)
      .then((r: any) => setState({ kind: "success", training: r.training_title, already: r.already_marked }))
      .catch((e) =>
        setState({ kind: "error", message: e?.response?.data?.detail ?? "Could not mark attendance" })
      );
  }, [accessToken, user, token, navigate]);

  return (
    <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center", p: 2, background: "linear-gradient(135deg,#4338ca 0%,#0d9488 100%)" }}>
      <Card sx={{ width: 420, maxWidth: "100%" }}>
        <CardContent sx={{ p: 4 }}>
          <Stack alignItems="center" spacing={2} textAlign="center">
            {state.kind === "loading" && (
              <>
                <CircularProgress />
                <Typography>Marking your attendance…</Typography>
              </>
            )}
            {state.kind === "success" && (
              <>
                {state.already ? (
                  <HourglassEmpty sx={{ fontSize: 56, color: "warning.main" }} />
                ) : (
                  <CheckCircle sx={{ fontSize: 56, color: "success.main" }} />
                )}
                <Typography variant="h5">
                  {state.already ? "Already marked" : "Attendance marked!"}
                </Typography>
                <Typography color="text.secondary">
                  {state.already
                    ? `Your attendance for ${state.training} was already recorded.`
                    : `You're marked present for ${state.training}.`}
                </Typography>
                <Button variant="contained" onClick={() => navigate("/attendance/mine")}>
                  View my attendance
                </Button>
              </>
            )}
            {state.kind === "error" && (
              <>
                <ErrorOutline sx={{ fontSize: 56, color: "error.main" }} />
                <Typography variant="h5">Couldn't check in</Typography>
                <Typography color="text.secondary">{state.message}</Typography>
                <Button variant="outlined" onClick={() => navigate("/")}>Go to dashboard</Button>
              </>
            )}
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
