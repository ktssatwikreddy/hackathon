import { Add, Delete, Edit } from "@mui/icons-material";
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  MenuItem,
  Pagination,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useForm } from "react-hook-form";

import ConfirmDialog from "../components/ConfirmDialog";
import { useDepartments, useUserMutations, useUsers } from "../hooks";
import type { Role, User } from "../types";

interface UserForm {
  employee_code: string;
  name: string;
  email: string;
  password?: string;
  role: Role;
  department_id: string;
}

export default function Users() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState<string>("");
  const { data, isLoading } = useUsers({ page, size: 10, search: search || undefined, role: role || undefined });
  const { data: departments } = useDepartments();
  const { create, update, remove } = useUserMutations();

  const [editing, setEditing] = useState<User | null>(null);
  const [open, setOpen] = useState(false);
  const [toDelete, setToDelete] = useState<User | null>(null);
  const { register, handleSubmit, reset } = useForm<UserForm>();

  const openCreate = () => {
    setEditing(null);
    reset({ employee_code: "", name: "", email: "", password: "", role: "employee", department_id: "" });
    setOpen(true);
  };
  const openEdit = (u: User) => {
    setEditing(u);
    reset({
      employee_code: u.employee_code,
      name: u.name,
      email: u.email,
      password: "",
      role: u.role,
      department_id: u.department_id ? String(u.department_id) : "",
    });
    setOpen(true);
  };

  const onSubmit = (form: UserForm) => {
    const body: Record<string, unknown> = {
      name: form.name,
      email: form.email,
      role: form.role,
      department_id: form.department_id ? Number(form.department_id) : null,
    };
    if (form.password) body.password = form.password;
    if (editing) {
      update.mutate({ id: editing.id, body });
    } else {
      body.employee_code = form.employee_code;
      create.mutate({ ...body, password: form.password || "Changeme@123" });
    }
    setOpen(false);
  };

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Users</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={openCreate}>New User</Button>
      </Stack>

      <Stack direction="row" spacing={2} mb={2}>
        <TextField
          size="small"
          label="Search"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        />
        <TextField
          size="small"
          select
          label="Role"
          value={role}
          onChange={(e) => { setRole(e.target.value); setPage(1); }}
          sx={{ width: 180 }}
        >
          <MenuItem value="">All roles</MenuItem>
          <MenuItem value="super_admin">Super Admin</MenuItem>
          <MenuItem value="trainer">Trainer</MenuItem>
          <MenuItem value="employee">Employee</MenuItem>
        </TextField>
      </Stack>

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Code</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow><TableCell colSpan={5}>Loading…</TableCell></TableRow>
            )}
            {data?.items.length === 0 && (
              <TableRow><TableCell colSpan={5}>No users found.</TableCell></TableRow>
            )}
            {data?.items.map((u) => (
              <TableRow key={u.id} hover>
                <TableCell>{u.employee_code}</TableCell>
                <TableCell>{u.name}</TableCell>
                <TableCell>{u.email}</TableCell>
                <TableCell><Chip size="small" label={u.role.replace("_", " ")} /></TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => openEdit(u)}><Edit fontSize="small" /></IconButton>
                  <IconButton size="small" color="error" onClick={() => setToDelete(u)}><Delete fontSize="small" /></IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {data && data.pages > 1 && (
        <Stack alignItems="center" mt={2}>
          <Pagination count={data.pages} page={page} onChange={(_, p) => setPage(p)} />
        </Stack>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editing ? "Edit User" : "New User"}</DialogTitle>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogContent>
            <Stack spacing={2} mt={1}>
              {!editing && <TextField label="Employee Code" fullWidth {...register("employee_code")} />}
              <TextField label="Name" fullWidth {...register("name")} />
              <TextField label="Email" type="email" fullWidth {...register("email")} />
              <TextField label={editing ? "New Password (optional)" : "Password"} type="password" fullWidth {...register("password")} />
              <TextField select label="Role" fullWidth defaultValue="employee" {...register("role")}>
                <MenuItem value="super_admin">Super Admin</MenuItem>
                <MenuItem value="trainer">Trainer</MenuItem>
                <MenuItem value="employee">Employee</MenuItem>
              </TextField>
              <TextField select label="Department" fullWidth defaultValue="" {...register("department_id")}>
                <MenuItem value="">None</MenuItem>
                {departments?.map((d) => <MenuItem key={d.id} value={String(d.id)}>{d.name}</MenuItem>)}
              </TextField>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained">{editing ? "Save" : "Create"}</Button>
          </DialogActions>
        </form>
      </Dialog>

      <ConfirmDialog
        open={!!toDelete}
        title="Delete user"
        message={`Delete ${toDelete?.name}? This cannot be undone.`}
        confirmText="Delete"
        onClose={() => setToDelete(null)}
        onConfirm={() => toDelete && remove.mutate(toDelete.id)}
      />
    </Box>
  );
}
