import { Box, Button, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

export default function NotFound() {
  const navigate = useNavigate();
  return (
    <Box sx={{ display: "grid", placeItems: "center", height: "60vh", textAlign: "center" }}>
      <Box>
        <Typography variant="h2" color="primary">404</Typography>
        <Typography color="text.secondary" mb={2}>This page doesn't exist.</Typography>
        <Button variant="contained" onClick={() => navigate("/")}>Go home</Button>
      </Box>
    </Box>
  );
}
