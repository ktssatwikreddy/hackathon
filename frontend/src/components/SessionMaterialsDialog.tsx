import { Download, UploadFile } from "@mui/icons-material";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import { type Material, materialsApi } from "../api/resources";
import { useAuth } from "../store/auth";

interface Props {
  sessionId: number | null;
  sessionTitle: string;
  onClose: () => void;
}

export default function SessionMaterialsDialog({ sessionId, sessionTitle, onClose }: Props) {
  const user = useAuth((s) => s.user);
  const isStaff = user?.role === "super_admin" || user?.role === "trainer";
  const [materials, setMaterials] = useState<Material[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = () => {
    if (sessionId) materialsApi.list(sessionId).then(setMaterials).catch(() => setMaterials([]));
  };
  useEffect(() => {
    if (sessionId) refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const upload = async () => {
    if (!sessionId || !file) return;
    setBusy(true);
    try {
      await materialsApi.upload(sessionId, file, title || file.name);
      setFile(null);
      setTitle("");
      refresh();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={sessionId !== null} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Files — {sessionTitle}</DialogTitle>
      <DialogContent>
        <List dense>
          {materials.length === 0 && <Typography color="text.secondary">No files yet.</Typography>}
          {materials.map((m) => (
            <ListItem
              key={m.id}
              secondaryAction={
                <IconButton edge="end" onClick={() => materialsApi.download(m.id, m.filename)}>
                  <Download />
                </IconButton>
              }
            >
              <ListItemText primary={m.title} secondary={m.filename} />
            </ListItem>
          ))}
        </List>

        {isStaff && (
          <Stack spacing={1.5} mt={2}>
            <Typography variant="subtitle2">Add a file</Typography>
            <Button component="label" variant="outlined" startIcon={<UploadFile />}>
              {file ? file.name : "Choose file"}
              <input hidden type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            </Button>
            <TextField size="small" label="Title (optional)" value={title} onChange={(e) => setTitle(e.target.value)} />
            <Button variant="contained" disabled={!file || busy} onClick={upload}>
              {busy ? "Uploading…" : "Upload"}
            </Button>
          </Stack>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
