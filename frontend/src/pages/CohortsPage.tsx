import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  Users,
  Plus,
  Trash2,
  X,
  ChevronDown,
  ChevronRight,
  Sparkles,
  GitBranch,
  Split,
  Layers,
} from 'lucide-react';
import { academicsService } from '../services/academics';
import { Cohort, InstructionGroup, Branch, AcademicTerm } from '../types';

const cohortSchema = z.object({
  branch: z.coerce.number().min(1, 'Please select a branch'),
  term: z.coerce.number().min(1, 'Please select an academic term'),
  semester_no: z.coerce.number().min(1, 'Min 1'),
  section_code: z.string().min(1, 'Section is required (e.g. A, B)').max(10),
  student_count: z.coerce.number().min(1).max(250),
});

type CohortFormData = z.infer<typeof cohortSchema>;

export const CohortsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedBranchId, setSelectedBranchId] = useState<number | undefined>();
  const [selectedTermId, setSelectedTermId] = useState<number | undefined>();
  const [expandedCohortIds, setExpandedCohortIds] = useState<Set<number>>(new Set());
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newGroupCohortId, setNewGroupCohortId] = useState<number | null>(null);
  const [groupCode, setGroupCode] = useState('');
  const [groupSize, setGroupSize] = useState(30);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Queries
  const { data: branches = [] } = useQuery({
    queryKey: ['branches'],
    queryFn: () => academicsService.getBranches(),
  });

  const { data: terms = [] } = useQuery({
    queryKey: ['academic-terms'],
    queryFn: () => academicsService.getAcademicTerms(),
  });

  const { data: cohorts = [], isLoading } = useQuery({
    queryKey: ['cohorts', selectedBranchId, selectedTermId],
    queryFn: () =>
      academicsService.getCohorts({
        branch: selectedBranchId,
        term: selectedTermId,
      }),
  });

  const activeBranch = branches.find((b) => b.id === selectedBranchId) || branches[0];

  // Form
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<CohortFormData>({
    resolver: zodResolver(cohortSchema),
    defaultValues: {
      branch: branches[0]?.id || 0,
      term: terms[0]?.id || 0,
      semester_no: 1,
      section_code: 'A',
      student_count: 60,
    },
  });

  const selectedFormBranchId = watch('branch');
  const formBranch = branches.find((b) => b.id === Number(selectedFormBranchId)) || activeBranch;

  // Mutations
  const createCohortMutation = useMutation({
    mutationFn: (data: Partial<Cohort>) => academicsService.createCohort(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cohorts'] });
      setIsModalOpen(false);
      reset();
    },
    onError: (err: any) => {
      const msg = err.response?.data?.semester_no?.[0] || err.response?.data?.non_field_errors?.[0] || err.response?.data?.detail || 'Failed to create cohort.';
      setErrorMessage(msg);
    },
  });

  const deleteCohortMutation = useMutation({
    mutationFn: (id: number) => academicsService.deleteCohort(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cohorts'] }),
  });

  const generateGroupsMutation = useMutation({
    mutationFn: ({ cohortId, type }: { cohortId: number; type: 'SPLIT' | 'SINGLE' }) =>
      academicsService.generateGroups(cohortId, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cohorts'] });
    },
  });

  const createGroupMutation = useMutation({
    mutationFn: (data: Partial<InstructionGroup>) => academicsService.createInstructionGroup(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cohorts'] });
      setNewGroupCohortId(null);
      setGroupCode('');
    },
  });

  const deleteGroupMutation = useMutation({
    mutationFn: (id: number) => academicsService.deleteInstructionGroup(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cohorts'] }),
  });

  const toggleExpand = (id: number) => {
    setExpandedCohortIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const openCreateModal = () => {
    reset({
      branch: selectedBranchId || branches[0]?.id || 0,
      term: selectedTermId || terms[0]?.id || 0,
      semester_no: 1,
      section_code: 'A',
      student_count: 60,
    });
    setErrorMessage(null);
    setIsModalOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary-50 dark:bg-primary-950/70 text-primary-700 dark:text-primary-300 mb-2">
            <Users className="w-3.5 h-3.5" />
            <span>Student Cohorts & Batches</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Cohorts & Lab Groups</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Organize student cohorts by branch, semester, and section. Divide into lab batches (e.g. A-L1, A-L2) for laboratory scheduling.
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-primary-600 text-white hover:bg-primary-700 shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Cohort</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-wrap items-center gap-4">
        <div className="min-w-[200px]">
          <label className="block text-[11px] font-semibold text-slate-500 mb-1">Filter by Branch</label>
          <select
            value={selectedBranchId || ''}
            onChange={(e) => setSelectedBranchId(e.target.value ? Number(e.target.value) : undefined)}
            className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
          >
            <option value="">All Branches</option>
            {branches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name} ({b.code})
              </option>
            ))}
          </select>
        </div>

        <div className="min-w-[200px]">
          <label className="block text-[11px] font-semibold text-slate-500 mb-1">Filter by Academic Term</label>
          <select
            value={selectedTermId || ''}
            onChange={(e) => setSelectedTermId(e.target.value ? Number(e.target.value) : undefined)}
            className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
          >
            <option value="">All Terms</option>
            {terms.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Cohorts List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading cohorts...</div>
        ) : cohorts.length === 0 ? (
          <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-500 text-xs">
            No cohorts found. Click "Add Cohort" above.
          </div>
        ) : (
          cohorts.map((cohort) => {
            const isExpanded = expandedCohortIds.has(cohort.id);
            const groups = cohort.instruction_groups || [];
            return (
              <div
                key={cohort.id}
                className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm transition-all"
              >
                {/* Cohort Header Bar */}
                <div className="p-4 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => toggleExpand(cohort.id)}
                      className="p-1 text-slate-400 hover:text-slate-600 rounded transition-colors"
                    >
                      {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </button>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-900 dark:text-white">
                          {cohort.branch_code} — Semester {cohort.semester_no}, Section {cohort.section_code}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-primary-100 text-primary-800 dark:bg-primary-950 dark:text-primary-300">
                          {cohort.term_name}
                        </span>
                      </div>
                      <span className="text-xs text-slate-500 block mt-0.5">
                        {cohort.student_count} Students • {groups.length} Lab/Instruction Group(s)
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => generateGroupsMutation.mutate({ cohortId: cohort.id, type: 'SPLIT' })}
                      title="Auto-create 2 equal lab groups (e.g. A-L1 and A-L2)"
                      className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition-colors flex items-center gap-1.5"
                    >
                      <Split className="w-3.5 h-3.5" />
                      <span>Auto Split (L1/L2)</span>
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Delete cohort ${cohort.branch_code} Sem ${cohort.semester_no} Sec ${cohort.section_code}?`)) {
                          deleteCohortMutation.mutate(cohort.id);
                        }
                      }}
                      className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Expandable Lab Groups Panel */}
                {isExpanded && (
                  <div className="border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        Instruction & Lab Groups (§5.2 Architecture Spec)
                      </span>
                      <button
                        onClick={() => setNewGroupCohortId(cohort.id)}
                        className="text-xs text-primary-600 hover:text-primary-700 font-semibold"
                      >
                        + Add Custom Batch
                      </button>
                    </div>

                    {groups.length === 0 ? (
                      <p className="text-xs text-slate-400 py-2">
                        No groups defined. Click "Auto Split (L1/L2)" to generate 2 batches or add manually.
                      </p>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        {groups.map((grp) => (
                          <div
                            key={grp.id}
                            className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs"
                          >
                            <div>
                              <span className="font-bold text-slate-900 dark:text-white font-mono">
                                {grp.code}
                              </span>
                              <span className="text-slate-500 text-[11px] block">
                                {grp.name || 'Lab Batch'} • {grp.size} students
                              </span>
                            </div>
                            <button
                              onClick={() => deleteGroupMutation.mutate(grp.id)}
                              className="text-slate-400 hover:text-rose-600 p-1"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* New Group Inline Form */}
                    {newGroupCohortId === cohort.id && (
                      <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-primary-200 dark:border-primary-800 flex items-center gap-3 text-xs">
                        <input
                          type="text"
                          placeholder="Group code (e.g. A-L3)"
                          value={groupCode}
                          onChange={(e) => setGroupCode(e.target.value)}
                          className="px-2.5 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                        />
                        <input
                          type="number"
                          placeholder="Batch Size"
                          value={groupSize}
                          onChange={(e) => setGroupSize(Number(e.target.value))}
                          className="w-24 px-2.5 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                        />
                        <button
                          onClick={() => {
                            if (!groupCode) return;
                            createGroupMutation.mutate({
                              cohort: cohort.id,
                              code: groupCode,
                              size: groupSize,
                              name: `Batch ${groupCode}`,
                            });
                          }}
                          className="px-3 py-1.5 rounded bg-primary-600 text-white font-semibold"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setNewGroupCohortId(null)}
                          className="px-2 py-1.5 text-slate-500"
                        >
                          Cancel
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Add Cohort Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-900 dark:text-white">Add Student Cohort</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            {errorMessage && (
              <div className="p-3 text-xs rounded-lg bg-rose-50 text-rose-700 dark:bg-rose-950/50">
                {errorMessage}
              </div>
            )}

            <form onSubmit={handleSubmit((d) => createCohortMutation.mutate(d))} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold block mb-1">Branch</label>
                <select
                  {...register('branch')}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                >
                  {branches.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name} ({b.code}) — Max Sem: {b.max_semesters}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="font-semibold block mb-1">Academic Term</label>
                <select
                  {...register('term')}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                >
                  {terms.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold block mb-1">
                    Semester No (1..{formBranch?.max_semesters || 8})
                  </label>
                  <input
                    type="number"
                    min="1"
                    max={formBranch?.max_semesters || 8}
                    {...register('semester_no')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                  />
                  {errors.semester_no && <p className="text-rose-500 mt-1">{errors.semester_no.message}</p>}
                </div>

                <div>
                  <label className="font-semibold block mb-1">Section Code</label>
                  <input
                    type="text"
                    placeholder="e.g. A, B, C"
                    {...register('section_code')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 uppercase"
                  />
                </div>
              </div>

              <div>
                <label className="font-semibold block mb-1">Student Count</label>
                <input
                  type="number"
                  {...register('student_count')}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                />
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
                  {isSubmitting ? 'Creating...' : 'Create Cohort'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
