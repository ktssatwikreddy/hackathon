import { Add, Delete, Edit } from "@mui/icons-material";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
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
import { useDepartmentMutations, useDepartments } from "../hooks";
import type { Department } from "../types";

interface DeptForm {
  name: string;
  description: string;
}

export default function Departments() {
  const { data, isLoading } = useDepartments();
  const { create, update, remove } = useDepartmentMutations();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Department | null>(null);
  const [toDelete, setToDelete] = useState<Department | null>(null);
  const { register, handleSubmit, reset } = useForm<DeptForm>();

  const openCreate = () => { setEditing(null); reset({ name: "", description: "" }); setOpen(true); };
  const openEdit = (d: Department) => { setEditing(d); reset({ name: d.name, description: d.description ?? "" }); setOpen(true); };

  const onSubmit = (form: DeptForm) => {
    const body = { name: form.name, description: form.description };
    if (editing) update.mutate({ id: editing.id, body });
    else create.mutate(body);
    setOpen(false);
  };

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Departments</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={openCreate}>New Department</Button>
      </Stack>

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && <TableRow><TableCell colSpan={3}>Loading…</TableCell></TableRow>}
            {data?.length === 0 && <TableRow><TableCell colSpan={3}>No departments yet.</TableCell></TableRow>}
            {data?.map((d) => (
              <TableRow key={d.id} hover>
                <TableCell>{d.name}</TableCell>
                <TableCell>{d.description}</TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => openEdit(d)}><Edit fontSize="small" /></IconButton>
                  <IconButton size="small" color="error" onClick={() => setToDelete(d)}><Delete fontSize="small" /></IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editing ? "Edit Department" : "New Department"}</DialogTitle>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogContent>
            <Stack spacing={2} mt={1}>
              <TextField label="Name" fullWidth {...register("name")} />
              <TextField label="Description" fullWidth multiline rows={3} {...register("description")} />
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
        title="Delete department"
        message={`Delete ${toDelete?.name}?`}
        confirmText="Delete"
        onClose={() => setToDelete(null)}
        onConfirm={() => toDelete && remove.mutate(toDelete.id)}
      />
    </Box>
  );
}
