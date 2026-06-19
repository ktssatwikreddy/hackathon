import { Box, Card, CardContent, Grid, Stack, Typography } from "@mui/material";

import { useAuth } from "../store/auth";

export default function Profile() {
  const user = useAuth((s) => s.user)!;
  const rows: [string, string][] = [
    ["Name", user.name],
    ["Email", user.email],
    ["Employee Code", user.employee_code],
    ["Role", user.role.replace("_", " ")],
    ["Designation", user.designation ?? "—"],
    ["Phone", user.phone ?? "—"],
    ["Joined", user.joining_date ?? "—"],
  ];

  return (
    <Box>
      <Typography variant="h4" mb={2}>Profile</Typography>
      <Card variant="outlined" sx={{ maxWidth: 640 }}>
        <CardContent>
          <Grid container spacing={2}>
            {rows.map(([k, v]) => (
              <Grid item xs={12} sm={6} key={k}>
                <Stack>
                  <Typography variant="caption" color="text.secondary">{k}</Typography>
                  <Typography>{v}</Typography>
                </Stack>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
}
