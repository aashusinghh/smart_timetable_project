import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  GitBranch,
  Plus,
  Edit2,
  Trash2,
  X,
  AlertCircle,
  Search,
  Filter,
  GraduationCap,
} from 'lucide-react';
import { academicsService, CreateBranchInput } from '../services/academics';
import { Branch } from '../types';

const branchSchema = z.object({
  department: z.coerce.number().min(1, 'Please select a department'),
  code: z.string().min(2, 'Code must be at least 2 characters').max(30, 'Code too long'),
  name: z.string().min(3, 'Name must be at least 3 characters').max(150),
  degree_name: z.string().min(2, 'Degree name is required').max(100),
  max_semesters: z.coerce.number().min(1, 'Min 1 semester').max(12, 'Max 12 semesters'),
  is_active: z.boolean().default(true),
});

type BranchFormData = z.infer<typeof branchSchema>;

export const BranchesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedDeptId, setSelectedDeptId] = useState<number | undefined>(undefined);
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingBranch, setEditingBranch] = useState<Branch | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fetch departments for dropdowns & filters
  const { data: departments = [] } = useQuery({
    queryKey: ['departments'],
    queryFn: academicsService.getDepartments,
  });

  // Fetch branches with optional department filter
  const { data: branches = [], isLoading, error } = useQuery({
    queryKey: ['branches', selectedDeptId],
    queryFn: () => academicsService.getBranches(selectedDeptId),
  });

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<BranchFormData>({
    resolver: zodResolver(branchSchema),
    defaultValues: {
      department: departments[0]?.id || 0,
      code: '',
      name: '',
      degree_name: 'B.Tech',
      max_semesters: 8,
      is_active: true,
    },
  });

  const openCreateModal = () => {
    setEditingBranch(null);
    reset({
      department: selectedDeptId || departments[0]?.id || 0,
      code: '',
      name: '',
      degree_name: 'B.Tech',
      max_semesters: 8,
      is_active: true,
    });
    setErrorMessage(null);
    setIsModalOpen(true);
  };

  const openEditModal = (branch: Branch) => {
    setEditingBranch(branch);
    setValue('department', branch.department);
    setValue('code', branch.code);
    setValue('name', branch.name);
    setValue('degree_name', branch.degree_name);
    setValue('max_semesters', branch.max_semesters);
    setValue('is_active', branch.is_active);
    setErrorMessage(null);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingBranch(null);
    reset();
    setErrorMessage(null);
  };

  // Quick preset helper when degree is selected
  const handleDegreePreset = (degree: string) => {
    setValue('degree_name', degree);
    if (degree === 'B.Tech') setValue('max_semesters', 8);
    else if (degree === 'MCA') setValue('max_semesters', 6);
    else if (degree === 'M.Tech') setValue('max_semesters', 4);
  };

  const createMutation = useMutation({
    mutationFn: (data: CreateBranchInput) => academicsService.createBranch(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches'] });
      queryClient.invalidateQueries({ queryKey: ['departments'] });
      closeModal();
    },
    onError: (err: any) => {
      const msg =
        err.response?.data?.non_field_errors?.[0] ||
        err.response?.data?.code?.[0] ||
        err.response?.data?.detail ||
        'Failed to save branch.';
      setErrorMessage(msg);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CreateBranchInput> }) =>
      academicsService.updateBranch(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches'] });
      queryClient.invalidateQueries({ queryKey: ['departments'] });
      closeModal();
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || 'Failed to update branch.';
      setErrorMessage(msg);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => academicsService.deleteBranch(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches'] });
      queryClient.invalidateQueries({ queryKey: ['departments'] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to delete branch.');
    },
  });

  const onSubmit = (data: BranchFormData) => {
    setErrorMessage(null);
    if (editingBranch) {
      updateMutation.mutate({ id: editingBranch.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleDelete = (branch: Branch) => {
    if (window.confirm(`Are you sure you want to delete branch "${branch.name} (${branch.code})"?`)) {
      deleteMutation.mutate(branch.id);
    }
  };

  const filteredBranches = branches.filter(
    (b) =>
      b.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.degree_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <GitBranch className="w-6 h-6 text-emerald-600" />
            <span>Academic Branches & Degrees</span>
          </h1>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Define degree programmes and maximum semester lengths (e.g. B.Tech 8 sem, MCA 6 sem, M.Tech 4 sem).
          </p>
        </div>

        <button
          onClick={openCreateModal}
          disabled={departments.length === 0}
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-colors disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          <span>Add Branch</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search branches..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={selectedDeptId || ''}
            onChange={(e) => setSelectedDeptId(e.target.value ? Number(e.target.value) : undefined)}
            className="px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">All Departments</option>
            {departments.map((dept) => (
              <option key={dept.id} value={dept.id}>
                {dept.name} ({dept.code})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading branches...</div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-rose-500">Failed to load branches.</div>
        ) : filteredBranches.length === 0 ? (
          <div className="p-12 text-center">
            <GitBranch className="w-8 h-8 text-slate-300 dark:text-slate-700 mx-auto mb-2" />
            <p className="text-xs font-medium text-slate-600 dark:text-slate-400">No branches found.</p>
            <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
              Select or add an academic branch to get started.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-3">Code</th>
                  <th className="px-5 py-3">Branch Name</th>
                  <th className="px-5 py-3">Department</th>
                  <th className="px-5 py-3">Degree</th>
                  <th className="px-5 py-3 text-center">Max Semesters</th>
                  <th className="px-5 py-3 text-center">Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                {filteredBranches.map((branch) => (
                  <tr key={branch.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="px-5 py-3.5 font-mono font-semibold text-emerald-600 dark:text-emerald-400">
                      {branch.code}
                    </td>
                    <td className="px-5 py-3.5 font-medium text-slate-900 dark:text-white">
                      {branch.name}
                    </td>
                    <td className="px-5 py-3.5 text-slate-500 dark:text-slate-400">
                      <span className="font-semibold text-slate-700 dark:text-slate-300">{branch.department_code}</span>
                      <span className="text-[11px] block text-slate-400">{branch.department_name}</span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-400">
                        <GraduationCap className="w-3 h-3" />
                        {branch.degree_name}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-center font-semibold">
                      {branch.max_semesters} Semesters
                    </td>
                    <td className="px-5 py-3.5 text-center">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          branch.is_active
                            ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                        }`}
                      >
                        {branch.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right space-x-2">
                      <button
                        onClick={() => openEditModal(branch)}
                        className="p-1 rounded text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
                        title="Edit Branch"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(branch)}
                        className="p-1 rounded text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 transition-colors"
                        title="Delete Branch"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-md shadow-2xl p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                {editingBranch ? 'Edit Branch' : 'Add New Branch'}
              </h3>
              <button
                onClick={closeModal}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {errorMessage && (
              <div className="mt-4 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900/60 flex items-start gap-2.5 text-xs text-rose-700 dark:text-rose-300">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Parent Department
                </label>
                <select
                  {...register('department')}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                >
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.code})
                    </option>
                  ))}
                </select>
                {errors.department && (
                  <p className="mt-1 text-[11px] text-rose-500">{errors.department.message}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Branch Code (e.g. BTECH_CSE, MCA, MTECH_CSE)
                </label>
                <input
                  type="text"
                  placeholder="BTECH_CSE"
                  {...register('code')}
                  className={`w-full px-3 py-2 text-xs rounded-lg border bg-white dark:bg-slate-800 uppercase ${
                    errors.code ? 'border-rose-400' : 'border-slate-300 dark:border-slate-700'
                  }`}
                />
                {errors.code && (
                  <p className="mt-1 text-[11px] text-rose-500">{errors.code.message}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Branch Name
                </label>
                <input
                  type="text"
                  placeholder="B.Tech Computer Science & Engineering"
                  {...register('name')}
                  className={`w-full px-3 py-2 text-xs rounded-lg border bg-white dark:bg-slate-800 ${
                    errors.name ? 'border-rose-400' : 'border-slate-300 dark:border-slate-700'
                  }`}
                />
                {errors.name && (
                  <p className="mt-1 text-[11px] text-rose-500">{errors.name.message}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Degree Name
                  </label>
                  <input
                    type="text"
                    placeholder="B.Tech / MCA / M.Tech"
                    {...register('degree_name')}
                    className={`w-full px-3 py-2 text-xs rounded-lg border bg-white dark:bg-slate-800 ${
                      errors.degree_name ? 'border-rose-400' : 'border-slate-300 dark:border-slate-700'
                    }`}
                  />
                  {errors.degree_name && (
                    <p className="mt-1 text-[11px] text-rose-500">{errors.degree_name.message}</p>
                  )}
                  {/* Presets */}
                  <div className="flex gap-1 mt-1.5">
                    {['B.Tech', 'MCA', 'M.Tech'].map((preset) => (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => handleDegreePreset(preset)}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-600 dark:text-slate-300"
                      >
                        {preset}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Max Semesters
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    {...register('max_semesters')}
                    className={`w-full px-3 py-2 text-xs rounded-lg border bg-white dark:bg-slate-800 ${
                      errors.max_semesters ? 'border-rose-400' : 'border-slate-300 dark:border-slate-700'
                    }`}
                  />
                  {errors.max_semesters && (
                    <p className="mt-1 text-[11px] text-rose-500">{errors.max_semesters.message}</p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="branch_is_active"
                  {...register('is_active')}
                  className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                />
                <label htmlFor="branch_is_active" className="text-xs font-medium text-slate-700 dark:text-slate-300">
                  Active Branch
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-3.5 py-1.5 text-xs font-semibold rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-60"
                >
                  {isSubmitting ? 'Saving...' : editingBranch ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

