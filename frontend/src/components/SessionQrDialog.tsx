import { Autorenew, Block } from "@mui/icons-material";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import { type QrToken } from "../api/resources";

interface Props {
  token: QrToken | null;
  sessionTitle: string;
  onRegenerate: () => void;
  onRevoke: () => void;
  onClose: () => void;
}

function useCountdown(expiresAt: string | undefined): string {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  if (!expiresAt) return "";
  const ms = new Date(expiresAt).getTime() - now;
  if (ms <= 0) return "expired";
  const m = Math.floor(ms / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  return `${m}:${String(s).padStart(2, "0")}`;
}

export default function SessionQrDialog({ token, sessionTitle, onRegenerate, onRevoke, onClose }: Props) {
  const countdown = useCountdown(token?.expires_at);
  const expired = countdown === "expired";

  return (
    <Dialog open={!!token} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Attendance QR — {sessionTitle}</DialogTitle>
      <DialogContent>
        <Stack alignItems="center" spacing={1.5}>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            Students scan this with their phone camera to mark attendance.
          </Typography>
          {token && (
            <Box
              component="img"
              src={token.qr_png_base64}
              alt="Attendance QR"
              sx={{ width: 240, height: 240, opacity: expired ? 0.35 : 1 }}
            />
          )}
          <Typography variant="h6" color={expired ? "error.main" : "text.primary"}>
            {expired ? "Expired — regenerate" : `Expires in ${countdown}`}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ wordBreak: "break-all", textAlign: "center" }}>
            {token?.checkin_url}
          </Typography>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button color="error" startIcon={<Block />} onClick={onRevoke}>Revoke</Button>
        <Button startIcon={<Autorenew />} onClick={onRegenerate}>Regenerate</Button>
        <Button variant="contained" onClick={onClose}>Done</Button>
      </DialogActions>
    </Dialog>
  );
}
