import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  GraduationCap,
  Plus,
  Trash2,
  GitBranch,
  Layers,
  BookOpen,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { academicsService } from '../services/academics';
import { Branch, CurriculumItem, Course } from '../types';

export const CurriculumPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedBranchId, setSelectedBranchId] = useState<number | undefined>();
  const [selectedSemester, setSelectedSemester] = useState<number>(1);
  const [selectedCourseId, setSelectedCourseId] = useState<number | undefined>();
  const [isElective, setIsElective] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Queries
  const { data: branches = [] } = useQuery({
    queryKey: ['branches'],
    queryFn: () => academicsService.getBranches(),
  });

  const activeBranch = branches.find((b) => b.id === selectedBranchId) || branches[0];

  const { data: curriculumItems = [], isLoading } = useQuery({
    queryKey: ['curriculum', selectedBranchId || activeBranch?.id, selectedSemester],
    queryFn: () =>
      academicsService.getCurriculumItems({
        branch: selectedBranchId || activeBranch?.id,
        semester: selectedSemester,
      }),
    enabled: !!activeBranch,
  });

  const { data: allCourses = [] } = useQuery({
    queryKey: ['courses'],
    queryFn: () => academicsService.getCourses(),
  });

  // Mutations
  const addCurriculumMutation = useMutation({
    mutationFn: (data: Partial<CurriculumItem>) => academicsService.createCurriculumItem(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['curriculum'] });
      setSelectedCourseId(undefined);
      setErrorMessage(null);
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.non_field_errors?.[0] || err.response?.data?.detail || 'Failed to add course to curriculum.');
    },
  });

  const removeCurriculumMutation = useMutation({
    mutationFn: (id: number) => academicsService.deleteCurriculumItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['curriculum'] });
    },
  });

  const currentBranchId = selectedBranchId || activeBranch?.id;
  const maxSemesters = activeBranch?.max_semesters || 8;

  const onAddCourse = () => {
    if (!selectedCourseId || !currentBranchId) return;
    addCurriculumMutation.mutate({
      branch: currentBranchId,
      semester_no: selectedSemester,
      course: selectedCourseId,
      is_elective: isElective,
    });
  };

  const assignedCourseIds = new Set(curriculumItems.map((ci) => ci.course));
  const availableCourses = allCourses.filter((c) => !assignedCourseIds.has(c.id));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary-50 dark:bg-primary-950/70 text-primary-700 dark:text-primary-300 mb-2">
          <GraduationCap className="w-3.5 h-3.5" />
          <span>Curriculum Structure</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Branch Curriculum Builder</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Map required and elective courses from catalog to specific branch semesters.
        </p>
      </div>

      {/* Selectors Bar */}
      <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-wrap items-center gap-4">
        {/* Branch Selector */}
        <div className="min-w-[240px]">
          <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Select Branch</label>
          <select
            value={currentBranchId || ''}
            onChange={(e) => {
              setSelectedBranchId(Number(e.target.value));
              setSelectedSemester(1);
            }}
            className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white font-medium"
          >
            {branches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name} ({b.code}) — {b.degree_name}
              </option>
            ))}
          </select>
        </div>

        {/* Semester Buttons */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
            Semester (Max: {maxSemesters})
          </label>
          <div className="flex flex-wrap items-center gap-1.5">
            {Array.from({ length: maxSemesters }, (_, i) => i + 1).map((sem) => (
              <button
                key={sem}
                onClick={() => setSelectedSemester(sem)}
                className={`px-3 py-1 text-xs font-bold rounded-lg transition-colors ${
                  selectedSemester === sem
                    ? 'bg-primary-600 text-white shadow-sm'
                    : 'bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300'
                }`}
              >
                Sem {sem}
              </button>
            ))}
          </div>
        </div>
      </div>

      {errorMessage && (
        <div className="p-3 text-xs rounded-lg bg-rose-50 text-rose-700 dark:bg-rose-950/50">
          {errorMessage}
        </div>
      )}

      {/* Main Grid: Current Curriculum Items & Add Course Box */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Items in Semester */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                {activeBranch?.code} — Semester {selectedSemester} Curriculum
              </h2>
              <p className="text-xs text-slate-500">
                {curriculumItems.length} course(s) assigned
              </p>
            </div>
            <span className="text-xs font-bold text-primary-600 dark:text-primary-400">
              Total Credits:{' '}
              {curriculumItems.reduce((acc, curr) => acc + (curr.course_credit || 0), 0)}
            </span>
          </div>

          {isLoading ? (
            <div className="p-8 text-center text-xs text-slate-500">Loading curriculum...</div>
          ) : curriculumItems.length === 0 ? (
            <div className="p-12 text-center text-slate-400 text-xs">
              No courses mapped to Semester {selectedSemester} yet. Add one from the right panel.
            </div>
          ) : (
            <div className="space-y-2.5">
              {curriculumItems.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-xs"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.course_type === 'LAB'
                          ? 'bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300'
                          : 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300'
                      }`}
                    >
                      {item.course_type}
                    </span>
                    <div>
                      <span className="font-mono font-bold text-slate-900 dark:text-white">
                        {item.course_code}
                      </span>{' '}
                      <span className="text-slate-700 dark:text-slate-300">— {item.course_name}</span>
                      <span className="text-slate-400 text-[11px] block">
                        {item.course_credit} Credits {item.is_elective && '• Elective'}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      if (confirm(`Remove ${item.course_code} from curriculum?`)) {
                        removeCurriculumMutation.mutate(item.id);
                      }
                    }}
                    className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Col: Add Course Form */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white">Add Course to Semester</h2>
          <p className="text-xs text-slate-500">
            Select a course from university catalog to include in this semester.
          </p>

          <div className="space-y-3 text-xs">
            <div>
              <label className="font-semibold block mb-1">Select Catalog Course</label>
              <select
                value={selectedCourseId || ''}
                onChange={(e) => setSelectedCourseId(Number(e.target.value) || undefined)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
              >
                <option value="">-- Choose a Course --</option>
                {availableCourses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.code} — {c.name} ({c.course_type}, {c.credit}cr)
                  </option>
                ))}
              </select>
            </div>

            <label className="flex items-center gap-2 cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={isElective}
                onChange={(e) => setIsElective(e.target.checked)}
                className="rounded"
              />
              <span>Is Elective Course</span>
            </label>

            <button
              onClick={onAddCourse}
              disabled={!selectedCourseId || addCurriculumMutation.isPending}
              className="w-full py-2 rounded-lg bg-primary-600 text-white font-semibold shadow-sm hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              {addCurriculumMutation.isPending ? 'Adding...' : '+ Add to Curriculum'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
