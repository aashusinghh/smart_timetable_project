import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  UserCheck,
  Plus,
  Edit2,
  Trash2,
  X,
  Search,
  CalendarX2,
  Clock,
  Shield,
  Building,
  Mail,
  Award,
} from 'lucide-react';
import { facultyService, CreateProfessorInput } from '../services/faculty';
import { academicsService } from '../services/academics';
import { ProfessorListItem, ProfessorUnavailability, Department } from '../types';

const professorSchema = z.object({
  email: z.string().email('Valid university email is required'),
  full_name: z.string().min(3, 'Full name required').max(150),
  employee_code: z.string().optional(),
  password: z.string().optional(),
  department: z.coerce.number().min(1, 'Please select a department'),
  designation: z.string().min(2, 'Designation required').default('Assistant Professor'),
  max_hours_per_day: z.coerce.number().min(1).max(12).default(6),
});

type ProfessorFormData = z.infer<typeof professorSchema>;

const unavailSchema = z.object({
  weekday: z.coerce.number().min(1).max(7).optional().nullable(),
  specific_date: z.string().optional().nullable(),
  start_slot: z.coerce.number().min(1).max(8),
  end_slot: z.coerce.number().min(1).max(8),
  reason: z.string().min(3, 'Reason is required'),
});

type UnavailFormData = z.infer<typeof unavailSchema>;

export const ProfessorsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedDeptId, setSelectedDeptId] = useState<number | undefined>();
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProf, setEditingProf] = useState<ProfessorListItem | null>(null);
  const [unavailProf, setUnavailProf] = useState<ProfessorListItem | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Queries
  const { data: departments = [] } = useQuery({
    queryKey: ['departments'],
    queryFn: academicsService.getDepartments,
  });

  const { data: professors = [], isLoading } = useQuery({
    queryKey: ['professors', selectedDeptId],
    queryFn: () => facultyService.getProfessors(selectedDeptId),
  });

  const { data: unavailabilities = [], refetch: refetchUnavail } = useQuery({
    queryKey: ['professor-unavailabilities', unavailProf?.id],
    queryFn: () => (unavailProf ? facultyService.getUnavailability(unavailProf.id) : []),
    enabled: !!unavailProf,
  });

  // Forms
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<ProfessorFormData>({
    resolver: zodResolver(professorSchema),
    defaultValues: {
      email: '',
      full_name: '',
      employee_code: '',
      department: departments[0]?.id || 0,
      designation: 'Assistant Professor',
      max_hours_per_day: 6,
    },
  });

  const {
    register: regUnavail,
    handleSubmit: handleUnavailSubmit,
    reset: resetUnavail,
    formState: { isSubmitting: isSubmittingUnavail },
  } = useForm<UnavailFormData>({
    resolver: zodResolver(unavailSchema),
    defaultValues: {
      weekday: 1,
      specific_date: '',
      start_slot: 1,
      end_slot: 2,
      reason: 'Department Meeting',
    },
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: CreateProfessorInput) => facultyService.createProfessor(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['professors'] });
      setIsModalOpen(false);
      reset();
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.email?.[0] || err.response?.data?.detail || 'Failed to create professor.');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CreateProfessorInput> }) =>
      facultyService.updateProfessor(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['professors'] });
      setIsModalOpen(false);
      reset();
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.detail || 'Failed to update professor.');
    },
  });

  const addUnavailMutation = useMutation({
    mutationFn: (data: Partial<ProfessorUnavailability>) =>
      facultyService.addUnavailability(unavailProf!.id, data),
    onSuccess: () => {
      refetchUnavail();
      resetUnavail();
    },
  });

  const deleteUnavailMutation = useMutation({
    mutationFn: (id: number) => facultyService.deleteUnavailability(id),
    onSuccess: () => {
      refetchUnavail();
    },
  });

  const openCreateModal = () => {
    setEditingProf(null);
    reset({
      email: '',
      full_name: '',
      employee_code: '',
      department: selectedDeptId || departments[0]?.id || 0,
      designation: 'Assistant Professor',
      max_hours_per_day: 6,
    });
    setErrorMessage(null);
    setIsModalOpen(true);
  };

  const openEditModal = (p: ProfessorListItem) => {
    setEditingProf(p);
    setValue('email', p.email);
    setValue('full_name', p.full_name);
    setValue('employee_code', p.employee_code || '');
    setValue('department', p.department_id);
    setValue('designation', p.designation);
    setValue('max_hours_per_day', p.max_hours_per_day);
    setErrorMessage(null);
    setIsModalOpen(true);
  };

  const onSubmit = (data: ProfessorFormData) => {
    setErrorMessage(null);
    if (editingProf) {
      updateMutation.mutate({
        id: editingProf.id,
        data: {
          full_name: data.full_name,
          employee_code: data.employee_code,
          department: data.department,
          designation: data.designation,
          max_hours_per_day: data.max_hours_per_day,
        },
      });
    } else {
      createMutation.mutate(data as CreateProfessorInput);
    }
  };

  const filteredProfessors = professors.filter(
    (p) =>
      p.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.employee_code && p.employee_code.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary-50 dark:bg-primary-950/70 text-primary-700 dark:text-primary-300 mb-2">
            <UserCheck className="w-3.5 h-3.5" />
            <span>Faculty Management</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Professors & Faculty</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Manage university faculty profiles, daily teaching limits, department affiliations, and unavailable slots.
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-primary-600 text-white hover:bg-primary-700 shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Professor</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by name, email, or employee ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
          />
        </div>

        <select
          value={selectedDeptId || ''}
          onChange={(e) => setSelectedDeptId(e.target.value ? Number(e.target.value) : undefined)}
          className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
        >
          <option value="">All Departments</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name} ({d.code})
            </option>
          ))}
        </select>
      </div>

      {/* Professors Table */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading faculty members...</div>
        ) : filteredProfessors.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">No faculty members found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="px-5 py-3">Faculty Member</th>
                  <th className="px-5 py-3">Department</th>
                  <th className="px-5 py-3">Designation</th>
                  <th className="px-5 py-3">Daily Max Load</th>
                  <th className="px-5 py-3">Role</th>
                  <th className="px-5 py-3">Assignments</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredProfessors.map((prof) => {
                  const isCoord = prof.roles.includes('BRANCH_COORDINATOR');
                  return (
                    <tr key={prof.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 font-bold flex items-center justify-center">
                            {prof.full_name.charAt(0)}
                          </div>
                          <div>
                            <span className="font-bold text-slate-900 dark:text-white block">
                              {prof.full_name}
                            </span>
                            <span className="text-slate-400 text-[11px] font-mono">{prof.email}</span>
                            {prof.employee_code && (
                              <span className="text-[10px] text-slate-400 block font-mono">
                                ID: {prof.employee_code}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="font-medium text-slate-800 dark:text-slate-200">
                          {prof.department_name}
                        </span>
                        <span className="block text-[11px] text-slate-400 font-mono">
                          {prof.department_code}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-slate-600 dark:text-slate-300">
                        {prof.designation}
                      </td>
                      <td className="px-5 py-3.5 font-semibold text-slate-800 dark:text-slate-200">
                        {prof.max_hours_per_day} hrs / day
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-semibold ${
                            isCoord
                              ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                              : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                          }`}
                        >
                          {isCoord ? 'Coordinator' : 'Professor'}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-slate-500 font-medium">
                        {prof.assignments_count || 0} active
                      </td>
                      <td className="px-5 py-3.5 text-right space-x-2">
                        <button
                          onClick={() => setUnavailProf(prof)}
                          title="Set Unavailable Slots"
                          className="p-1.5 text-slate-500 hover:text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-950/50 rounded-lg transition-colors"
                        >
                          <CalendarX2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => openEditModal(prof)}
                          title="Edit Profile"
                          className="p-1.5 text-slate-500 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-950/50 rounded-lg transition-colors"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add / Edit Professor Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                {editingProf ? 'Edit Faculty Profile' : 'Add New Faculty Member'}
              </h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            {errorMessage && (
              <div className="p-3 text-xs rounded-lg bg-rose-50 text-rose-700 dark:bg-rose-950/50">
                {errorMessage}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold block mb-1">Full Name</label>
                <input
                  type="text"
                  placeholder="e.g. Dr. Alan Turing"
                  {...register('full_name')}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                />
                {errors.full_name && <p className="text-rose-500 mt-1">{errors.full_name.message}</p>}
              </div>

              <div>
                <label className="font-semibold block mb-1">University Email</label>
                <input
                  type="email"
                  disabled={!!editingProf}
                  placeholder="e.g. a.turing@university.edu"
                  {...register('email')}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 disabled:opacity-60"
                />
                {errors.email && <p className="text-rose-500 mt-1">{errors.email.message}</p>}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold block mb-1">Employee Code</label>
                  <input
                    type="text"
                    placeholder="e.g. EMP045"
                    {...register('employee_code')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                  />
                </div>
                <div>
                  <label className="font-semibold block mb-1">Department</label>
                  <select
                    {...register('department')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                  >
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.code})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold block mb-1">Designation</label>
                  <input
                    type="text"
                    placeholder="e.g. Associate Professor"
                    {...register('designation')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                  />
                </div>
                <div>
                  <label className="font-semibold block mb-1">Max Daily Load (hrs)</label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    {...register('max_hours_per_day')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-primary-600 text-white font-semibold shadow-sm hover:bg-primary-700"
                >
                  {isSubmitting ? 'Saving...' : editingProf ? 'Update Profile' : 'Create Professor'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Professor Unavailability Modal */}
      {unavailProf && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-white">
                  Unavailable Slots — {unavailProf.full_name}
                </h2>
                <p className="text-xs text-slate-500">
                  Slots marked unavailable will be strictly blocked during timetable scheduling across all branches.
                </p>
              </div>
              <button onClick={() => setUnavailProf(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* List */}
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {unavailabilities.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-3">No unavailable blocks registered.</p>
              ) : (
                unavailabilities.map((u) => (
                  <div
                    key={u.id}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs"
                  >
                    <div>
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        {u.specific_date ? `Date: ${u.specific_date}` : `Weekday ${u.weekday}`}
                      </span>
                      <span className="text-slate-500 block">
                        Slots {u.start_slot} to {u.end_slot} — {u.reason}
                      </span>
                    </div>
                    <button
                      onClick={() => deleteUnavailMutation.mutate(u.id)}
                      className="text-rose-500 hover:text-rose-700 p-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>

            {/* Add Form */}
            <form
              onSubmit={handleUnavailSubmit((data) => addUnavailMutation.mutate(data))}
              className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3 text-xs"
            >
              <h3 className="font-bold text-slate-800 dark:text-slate-200">Add Unavailable Time Block</h3>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-medium text-slate-500">Recurring Weekday</label>
                  <select {...regUnavail('weekday')} className="w-full px-2 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                    <option value="">None (Use Date)</option>
                    <option value="1">Monday</option>
                    <option value="2">Tuesday</option>
                    <option value="3">Wednesday</option>
                    <option value="4">Thursday</option>
                    <option value="5">Friday</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-500">Or Specific Date</label>
                  <input type="date" {...regUnavail('specific_date')} className="w-full px-2 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800" />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-[11px] font-medium text-slate-500">Start Slot (1-8)</label>
                  <input type="number" min="1" max="8" {...regUnavail('start_slot')} className="w-full px-2 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800" />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-500">End Slot (1-8)</label>
                  <input type="number" min="1" max="8" {...regUnavail('end_slot')} className="w-full px-2 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800" />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-500">Reason</label>
                  <input type="text" placeholder="Meeting / Leave" {...regUnavail('reason')} className="w-full px-2 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800" />
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={isSubmittingUnavail}
                  className="px-3 py-1.5 rounded-lg bg-amber-600 text-white font-semibold hover:bg-amber-700"
                >
                  Add Block
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
