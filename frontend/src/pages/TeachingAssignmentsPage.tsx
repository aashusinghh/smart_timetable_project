import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  UserCheck,
  Plus,
  Trash2,
  BookOpen,
  Users,
  CheckCircle,
  AlertCircle,
  Sparkles,
  Layers,
  X,
} from 'lucide-react';
import { academicsService } from '../services/academics';
import { facultyService } from '../services/faculty';
import {
  CourseOffering,
  TeachingAssignment,
  Cohort,
  AcademicTerm,
  ProfessorListItem,
} from '../types';

export const TeachingAssignmentsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedCohortId, setSelectedCohortId] = useState<number | undefined>();
  const [assigningOffering, setAssigningOffering] = useState<CourseOffering | null>(null);
  const [selectedProfId, setSelectedProfId] = useState<number | undefined>();
  const [selectedGroupId, setSelectedGroupId] = useState<number | undefined>();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Queries
  const { data: cohorts = [] } = useQuery({
    queryKey: ['cohorts'],
    queryFn: () => academicsService.getCohorts(),
  });

  const activeCohort = cohorts.find((c) => c.id === selectedCohortId) || cohorts[0];

  const { data: offerings = [], isLoading } = useQuery({
    queryKey: ['course-offerings', selectedCohortId || activeCohort?.id],
    queryFn: () =>
      academicsService.getCourseOfferings({
        cohort: selectedCohortId || activeCohort?.id,
      }),
    enabled: !!activeCohort,
  });

  const { data: assignments = [] } = useQuery({
    queryKey: ['teaching-assignments', selectedCohortId || activeCohort?.id],
    queryFn: () =>
      academicsService.getTeachingAssignments({
        cohort: selectedCohortId || activeCohort?.id,
      }),
    enabled: !!activeCohort,
  });

  const { data: professors = [] } = useQuery({
    queryKey: ['professors'],
    queryFn: () => facultyService.getProfessors(),
  });

  // Mutations
  const populateMutation = useMutation({
    mutationFn: (cohortId: number) => academicsService.populateFromCurriculum(cohortId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['course-offerings'] });
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.detail || 'Failed to populate offerings.');
    },
  });

  const createAssignmentMutation = useMutation({
    mutationFn: (data: Partial<TeachingAssignment>) => academicsService.createTeachingAssignment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teaching-assignments'] });
      queryClient.invalidateQueries({ queryKey: ['course-offerings'] });
      setAssigningOffering(null);
      setSelectedProfId(undefined);
      setSelectedGroupId(undefined);
      setErrorMessage(null);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.non_field_errors?.[0] || err.response?.data?.detail || 'Failed to assign professor.';
      setErrorMessage(msg);
    },
  });

  const deleteAssignmentMutation = useMutation({
    mutationFn: (id: number) => academicsService.deleteTeachingAssignment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teaching-assignments'] });
      queryClient.invalidateQueries({ queryKey: ['course-offerings'] });
    },
  });

  const currentCohortId = selectedCohortId || activeCohort?.id;

  const onAssignSubmit = () => {
    if (!assigningOffering || !selectedProfId) return;
    createAssignmentMutation.mutate({
      course_offering: assigningOffering.id,
      professor: selectedProfId,
      instruction_group: selectedGroupId || null,
      is_primary: true,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary-50 dark:bg-primary-950/70 text-primary-700 dark:text-primary-300 mb-2">
            <UserCheck className="w-3.5 h-3.5" />
            <span>Faculty Mappings</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Teaching Assignments</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Map faculty professors to cohort course offerings. The timetable optimizer will use these fixed mappings to schedule rooms and time slots.
          </p>
        </div>

        {activeCohort && (
          <button
            onClick={() => populateMutation.mutate(activeCohort.id)}
            disabled={populateMutation.isPending}
            className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            <span>Populate from Curriculum</span>
          </button>
        )}
      </div>

      {/* Cohort Selector */}
      <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center gap-4">
        <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Select Cohort:</label>
        <select
          value={currentCohortId || ''}
          onChange={(e) => setSelectedCohortId(Number(e.target.value))}
          className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white font-medium min-w-[280px]"
        >
          {cohorts.map((c) => (
            <option key={c.id} value={c.id}>
              {c.branch_code} Sem {c.semester_no} Sec {c.section_code} ({c.term_name})
            </option>
          ))}
        </select>
      </div>

      {/* Offerings and Teaching Assignment Cards */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading course offerings...</div>
        ) : offerings.length === 0 ? (
          <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 space-y-3">
            <BookOpen className="w-8 h-8 text-slate-400 mx-auto" />
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No course offerings for this cohort yet</p>
            <p className="text-xs text-slate-500">Click "Populate from Curriculum" above to auto-generate offerings from the branch semester syllabus.</p>
          </div>
        ) : (
          offerings.map((offering) => {
            const courseAssignments = assignments.filter((a) => a.course_offering === offering.id);
            const isLab = offering.course_type === 'LAB';
            return (
              <div
                key={offering.id}
                className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4"
              >
                {/* Offering Title */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-3">
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2.5 py-0.5 rounded text-[11px] font-bold ${
                        isLab
                          ? 'bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300'
                          : 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300'
                      }`}
                    >
                      {offering.course_type}
                    </span>
                    <div>
                      <h3 className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                        {offering.course_code} — {offering.course_name}
                      </h3>
                      <span className="text-xs text-slate-500">
                        {offering.course_credit} Credits • {courseAssignments.length} Assigned Professor(s)
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      setAssigningOffering(offering);
                      setSelectedProfId(undefined);
                      setSelectedGroupId(undefined);
                      setErrorMessage(null);
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Assign Faculty</span>
                  </button>
                </div>

                {/* Assigned Faculty List */}
                <div className="space-y-2">
                  {courseAssignments.length === 0 ? (
                    <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/40 text-xs text-amber-700 dark:text-amber-300 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      <span>Unassigned: A professor must be mapped before timetable scheduling.</span>
                    </div>
                  ) : (
                    courseAssignments.map((asgn) => (
                      <div
                        key={asgn.id}
                        className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 text-xs"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-950 text-primary-600 flex items-center justify-center font-bold">
                            {asgn.professor_name?.charAt(0) || 'P'}
                          </div>
                          <div>
                            <span className="font-bold text-slate-900 dark:text-white">
                              {asgn.professor_name}
                            </span>{' '}
                            <span className="text-slate-500 text-[11px]">({asgn.professor_email})</span>
                            <span className="text-slate-400 block text-[11px]">
                              Scope:{' '}
                              {asgn.group_code ? (
                                <span className="font-mono font-semibold text-primary-600">
                                  Lab Group [{asgn.group_code}]
                                </span>
                              ) : (
                                'Entire Cohort / Full Lecture'
                              )}
                            </span>
                          </div>
                        </div>

                        <button
                          onClick={() => deleteAssignmentMutation.mutate(asgn.id)}
                          className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Assign Professor Modal */}
      {assigningOffering && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-white">
                  Assign Faculty Member
                </h2>
                <p className="text-xs text-slate-500">{assigningOffering.course_code} — {assigningOffering.course_name}</p>
              </div>
              <button onClick={() => setAssigningOffering(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            {errorMessage && (
              <div className="p-3 text-xs rounded-lg bg-rose-50 text-rose-700 dark:bg-rose-950/50">
                {errorMessage}
              </div>
            )}

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold block mb-1">Select Professor</label>
                <select
                  value={selectedProfId || ''}
                  onChange={(e) => setSelectedProfId(Number(e.target.value) || undefined)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                >
                  <option value="">-- Choose Professor --</option>
                  {professors.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.full_name} ({p.designation}, {p.department_code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="font-semibold block mb-1">
                  Target Student Group (Optional for Labs)
                </label>
                <select
                  value={selectedGroupId || ''}
                  onChange={(e) => setSelectedGroupId(Number(e.target.value) || undefined)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                >
                  <option value="">Entire Cohort (All Students)</option>
                  {activeCohort?.instruction_groups?.map((grp) => (
                    <option key={grp.id} value={grp.id}>
                      Lab Group {grp.code} ({grp.size} students)
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-slate-400 mt-1">
                  Leave as "Entire Cohort" for theory lectures. Choose a lab group for divided practical sessions.
                </p>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setAssigningOffering(null)}
                  className="px-4 py-2 rounded-lg text-slate-600"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={onAssignSubmit}
                  disabled={!selectedProfId || createAssignmentMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-primary-600 text-white font-semibold hover:bg-primary-700 disabled:opacity-50"
                >
                  {createAssignmentMutation.isPending ? 'Assigning...' : 'Confirm Assignment'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
