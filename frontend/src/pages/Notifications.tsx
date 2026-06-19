import { DoneAll } from "@mui/icons-material";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  Typography,
} from "@mui/material";

import { useNotificationMutations, useNotifications } from "../hooks";

export default function Notifications() {
  const { data } = useNotifications();
  const { markRead, readAll } = useNotificationMutations();

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Notifications</Typography>
        <Button startIcon={<DoneAll />} onClick={() => readAll.mutate()}>Mark all read</Button>
      </Stack>

      <Stack spacing={1.5}>
        {data?.length === 0 && <Typography color="text.secondary">You're all caught up.</Typography>}
        {data?.map((n) => (
          <Card key={n.id} variant="outlined" sx={{ bgcolor: n.is_read ? "transparent" : "#eef2ff" }}>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Stack direction="row" spacing={1} alignItems="center" mb={0.5}>
                    <Typography fontWeight={600}>{n.title}</Typography>
                    <Chip size="small" label={n.type} />
                    {!n.is_read && <Chip size="small" color="primary" label="new" />}
                  </Stack>
                  <Typography variant="body2" color="text.secondary">{n.message}</Typography>
                  <Typography variant="caption" color="text.secondary">{new Date(n.created_at).toLocaleString()}</Typography>
                </Box>
                {!n.is_read && (
                  <Button size="small" onClick={() => markRead.mutate(n.id)}>Mark read</Button>
                )}
              </Stack>
            </CardContent>
          </Card>
        ))}
      </Stack>
    </Box>
  );
}
