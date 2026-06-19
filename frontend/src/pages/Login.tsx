import { zodResolver } from "@hookform/resolvers/zod";
import { LockOutlined } from "@mui/icons-material";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";

import { authApi } from "../api/resources";
import { useAuth } from "../store/auth";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});
type FormData = z.infer<typeof schema>;

const DEMO = [
  { label: "Admin", email: "admin@tapms.com" },
  { label: "Trainer", email: "trainer1@tapms.com" },
  { label: "Employee", email: "employee1@tapms.com" },
];

export default function Login() {
  const navigate = useNavigate();
  const setSession = useAuth((s) => s.setSession);
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { email: "admin@tapms.com", password: "Admin@123" },
  });

  const onSubmit = async (data: FormData) => {
    setError(null);
    try {
      const resp = await authApi.login(data.email, data.password);
      setSession(resp.access_token, resp.refresh_token, resp.user);
      navigate("/");
    } catch {
      setError("Invalid email or password.");
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        background: "linear-gradient(135deg,#4338ca 0%,#0d9488 100%)",
        p: 2,
      }}
    >
      <Card sx={{ width: 420, maxWidth: "100%" }}>
        <CardContent sx={{ p: 4 }}>
          <Stack alignItems="center" spacing={1} mb={2}>
            <Avatar sx={{ bgcolor: "primary.main" }}>
              <LockOutlined />
            </Avatar>
            <Typography variant="h5">TAPMS</Typography>
            <Typography variant="body2" color="text.secondary">
              Training Attendance & Performance Management
            </Typography>
          </Stack>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <form onSubmit={handleSubmit(onSubmit)}>
            <Stack spacing={2}>
              <TextField
                label="Email"
                fullWidth
                {...register("email")}
                error={!!errors.email}
                helperText={errors.email?.message}
              />
              <TextField
                label="Password"
                type="password"
                fullWidth
                {...register("password")}
                error={!!errors.password}
                helperText={errors.password?.message}
              />
              <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
                {isSubmitting ? "Signing in…" : "Sign in"}
              </Button>
            </Stack>
          </form>

          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 3, mb: 1 }}>
            Demo logins (password Admin@123 / Trainer@123 / Employee@123):
          </Typography>
          <Stack direction="row" spacing={1}>
            {DEMO.map((d) => (
              <Button
                key={d.email}
                size="small"
                variant="outlined"
                onClick={() => {
                  setValue("email", d.email);
                  setValue(
                    "password",
                    d.label === "Admin" ? "Admin@123" : d.label === "Trainer" ? "Trainer@123" : "Employee@123"
                  );
                }}
              >
                {d.label}
              </Button>
            ))}
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
