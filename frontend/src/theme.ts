import { createTheme } from "@mui/material/styles";

// A calm, professional indigo/teal palette — distinct from MUI defaults.
const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#4338ca", light: "#6366f1", dark: "#3730a3" },
    secondary: { main: "#0d9488" },
    background: { default: "#f5f6fa", paper: "#ffffff" },
    success: { main: "#16a34a" },
    warning: { main: "#d97706" },
    error: { main: "#dc2626" },
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: ["Inter", "Segoe UI", "Roboto", "system-ui", "sans-serif"].join(","),
    h4: { fontWeight: 700 },
    h5: { fontWeight: 700 },
    h6: { fontWeight: 600 },
  },
  components: {
    MuiCard: { defaultProps: { elevation: 0 }, styleOverrides: { root: { border: "1px solid #e6e8f0" } } },
    MuiButton: { defaultProps: { disableElevation: true }, styleOverrides: { root: { textTransform: "none", fontWeight: 600 } } },
    MuiAppBar: { defaultProps: { elevation: 0 } },
  },
});

export default theme;
