import {
  Analytics,
  Assignment,
  Badge as BadgeIcon,
  Business,
  CalendarMonth,
  Dashboard as DashboardIcon,
  EventNote,
  Explore,
  FactCheck,
  Inbox,
  Group,
  Insights,
  Logout,
  Notifications as NotificationsIcon,
  Person,
  School,
} from "@mui/icons-material";
import {
  AppBar,
  Avatar,
  Badge,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { useState, type ReactNode } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import { useNotifications } from "../hooks";
import { useAuth } from "../store/auth";
import type { Role } from "../types";

const DRAWER_WIDTH = 248;

interface NavItem {
  label: string;
  path: string;
  icon: ReactNode;
  roles: Role[];
}

const ALL: Role[] = ["super_admin", "trainer", "employee"];

const NAV: NavItem[] = [
  { label: "Dashboard", path: "/", icon: <DashboardIcon />, roles: ALL },
  { label: "Users", path: "/users", icon: <Group />, roles: ["super_admin"] },
  { label: "Departments", path: "/departments", icon: <Business />, roles: ["super_admin"] },
  { label: "Schedule Course", path: "/courses/new", icon: <EventNote />, roles: ["super_admin"] },
  { label: "Trainings", path: "/trainings", icon: <School />, roles: ALL },
  { label: "Browse Courses", path: "/browse", icon: <Explore />, roles: ["employee"] },
  { label: "Requests", path: "/requests", icon: <Inbox />, roles: ["super_admin", "trainer"] },
  { label: "Sessions", path: "/sessions", icon: <CalendarMonth />, roles: ["super_admin", "trainer"] },
  { label: "Mark Attendance", path: "/attendance/mark", icon: <FactCheck />, roles: ["super_admin", "trainer"] },
  { label: "My Attendance", path: "/attendance/mine", icon: <BadgeIcon />, roles: ["employee"] },
  { label: "Assessments", path: "/assessments", icon: <Assignment />, roles: ALL },
  { label: "AI Insights", path: "/ai", icon: <Insights />, roles: ALL },
  { label: "Reports", path: "/reports", icon: <Analytics />, roles: ["super_admin", "trainer", "employee"] },
];

export default function AppLayout() {
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);
  const navigate = useNavigate();
  const location = useLocation();
  const { data: notifications } = useNotifications(true);
  const [anchor, setAnchor] = useState<null | HTMLElement>(null);

  if (!user) return null;
  const items = NAV.filter((item) => item.roles.includes(user.role));
  const unread = notifications?.length ?? 0;

  return (
    <Box sx={{ display: "flex" }}>
      <AppBar
        position="fixed"
        color="inherit"
        sx={{ zIndex: (t) => t.zIndex.drawer + 1, borderBottom: "1px solid #e6e8f0" }}
      >
        <Toolbar>
          <School sx={{ color: "primary.main", mr: 1 }} />
          <Typography variant="h6" sx={{ flexGrow: 1, color: "primary.main" }}>
            TAPMS
          </Typography>
          <Tooltip title="Notifications">
            <IconButton onClick={() => navigate("/notifications")}>
              <Badge badgeContent={unread} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Tooltip>
          <IconButton onClick={(e) => setAnchor(e.currentTarget)} sx={{ ml: 1 }}>
            <Avatar sx={{ bgcolor: "primary.main", width: 34, height: 34 }}>
              {user.name.charAt(0)}
            </Avatar>
          </IconButton>
          <Menu anchorEl={anchor} open={!!anchor} onClose={() => setAnchor(null)}>
            <MenuItem disabled>
              <Typography variant="body2">
                {user.name} · {user.role.replace("_", " ")}
              </Typography>
            </MenuItem>
            <Divider />
            <MenuItem onClick={() => { setAnchor(null); navigate("/profile"); }}>
              <ListItemIcon><Person fontSize="small" /></ListItemIcon> Profile
            </MenuItem>
            <MenuItem onClick={() => { logout(); navigate("/login"); }}>
              <ListItemIcon><Logout fontSize="small" /></ListItemIcon> Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: DRAWER_WIDTH, boxSizing: "border-box" },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: "auto", py: 1 }}>
          <List>
            {items.map((item) => {
              const selected =
                item.path === "/" ? location.pathname === "/" : location.pathname.startsWith(item.path);
              return (
                <ListItemButton
                  key={item.path}
                  selected={selected}
                  onClick={() => navigate(item.path)}
                  sx={{ mx: 1, borderRadius: 2, mb: 0.5 }}
                >
                  <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.label} />
                </ListItemButton>
              );
            })}
          </List>
        </Box>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3, minHeight: "100vh", bgcolor: "background.default" }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
