import { Card, CardContent, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";

interface Props {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  color?: string;
  suffix?: string;
}

export default function StatCard({ label, value, icon, color = "#4338ca", suffix }: Props) {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Stack spacing={0.5}>
            <Typography variant="body2" color="text.secondary">
              {label}
            </Typography>
            <Typography variant="h4" sx={{ color }}>
              {value}
              {suffix && (
                <Typography component="span" variant="h6" color="text.secondary">
                  {suffix}
                </Typography>
              )}
            </Typography>
          </Stack>
          {icon && (
            <Stack
              sx={{
                bgcolor: `${color}14`,
                color,
                borderRadius: 2,
                p: 1,
              }}
            >
              {icon}
            </Stack>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
