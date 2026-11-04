import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Calendar,
  Layers,
  Check,
  X,
} from 'lucide-react';
import { timetableService } from '../services/timetable';
import { ScheduleVersion, ValidationSweepResponse } from '../types';

export const ScheduleReviewPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedVersionId, setSelectedVersionId] = useState<number | undefined>();
  const [successToast, setSuccessToast] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load all UNDER_REVIEW schedule versions
  const { data: allVersions = [], isLoading } = useQuery({
    queryKey: ['timetable-versions-review'],
    queryFn: () => timetableService.getVersions(),
  });

  const reviewVersions = allVersions.filter((v) => v.status === 'UNDER_REVIEW');
  const activeVersion = reviewVersions.find((v) => v.id === selectedVersionId) || reviewVersions[0];

  // Validation Sweep for active review version
  const {
    data: sweepResult,
    isLoading: isSweeping,
    refetch: refetchSweep,
  } = useQuery<ValidationSweepResponse>({
    queryKey: ['validation-sweep', activeVersion?.id],
    queryFn: () => timetableService.validateSweep(activeVersion.id),
    enabled: !!activeVersion,
  });

  // Publish mutation
  const publishMutation = useMutation({
    mutationFn: (id: number) => timetableService.publishSchedule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timetable-versions-review'] });
      queryClient.invalidateQueries({ queryKey: ['timetable-versions'] });
      setSuccessToast(`🎉 Successfully PUBLISHED schedule! Previous published version archived.`);
      setTimeout(() => setSuccessToast(null), 4000);
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.detail || 'Failed to publish schedule.');
    },
  });

  // Send back mutation
  const sendBackMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => timetableService.sendBackToDraft(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timetable-versions-review'] });
      queryClient.invalidateQueries({ queryKey: ['timetable-versions'] });
      setSuccessToast('Schedule returned to draft for coordinator adjustments.');
      setTimeout(() => setSuccessToast(null), 3000);
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.detail || 'Failed to send back.');
    },
  });

  return (
    <div className="space-y-6">
      {/* Toast */}
      {successToast && (
        <div className="fixed top-5 right-5 z-50 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 text-white text-xs font-semibold shadow-lg animate-bounce">
          <CheckCircle2 className="w-4 h-4" />
          <span>{successToast}</span>
        </div>
      )}

      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/70 text-indigo-700 dark:text-indigo-300 mb-2">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Administrative Publication Desk</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Schedule Review & Publication</h1>
        <p className="text-sm text-slate-500">
          Verify global university timetable coverage, inspect constraint sweeps, and officially publish semester schedules.
        </p>
      </div>

      {/* Error alert */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 flex items-start justify-between gap-3 text-xs text-rose-800 dark:text-rose-200">
          <div className="flex items-center gap-2 font-semibold">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-rose-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {reviewVersions.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
          <div className="w-12 h-12 rounded-full bg-emerald-50 dark:bg-emerald-950 text-emerald-600 mx-auto flex items-center justify-center">
            <Check className="w-6 h-6" />
          </div>
          <h2 className="text-base font-bold text-slate-800 dark:text-slate-100">No Schedules Awaiting Review</h2>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            All semester drafts have been approved or are currently being scheduled by branch coordinators.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Pending Review List */}
          <div className="lg:col-span-1 space-y-3">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1">
              Schedules Under Review ({reviewVersions.length})
            </h2>

            {reviewVersions.map((v) => {
              const isSelected = activeVersion?.id === v.id;
              return (
                <div
                  key={v.id}
                  onClick={() => setSelectedVersionId(v.id)}
                  className={`p-4 rounded-xl border text-xs cursor-pointer transition-all ${
                    isSelected
                      ? 'border-indigo-600 bg-indigo-50/40 dark:bg-indigo-950/30 shadow-md ring-2 ring-indigo-500/20'
                      : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-indigo-400'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-slate-900 dark:text-white text-sm">
                      {v.name || `Version ${v.version_no}`}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                      UNDER REVIEW
                    </span>
                  </div>

                  <p className="text-slate-600 dark:text-slate-400 font-medium">{v.term_name}</p>

                  <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
                    <span>{v.meetings_count || 0} Meetings</span>
                    <span>Rev {v.revision}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right: Validation & Publication Actions */}
          {activeVersion && (
            <div className="lg:col-span-2 space-y-5">
              <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-4">
                  <div>
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                      {activeVersion.name || `Version ${activeVersion.version_no}`} — Review Sweep
                    </h2>
                    <p className="text-xs text-slate-500">Academic Term: {activeVersion.term_name}</p>
                  </div>

                  <button
                    onClick={() => refetchSweep()}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-200 flex items-center gap-1.5 self-start"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isSweeping ? 'animate-spin' : ''}`} />
                    <span>Re-Run Validation</span>
                  </button>
                </div>

                {/* Sweep Verification Status Card */}
                {isSweeping ? (
                  <div className="p-8 text-center text-xs text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-500" />
                    Running authoritative conflict validation across all branch meetings...
                  </div>
                ) : sweepResult?.valid ? (
                  <div className="p-5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h3 className="font-bold text-sm text-emerald-900 dark:text-emerald-200">
                        Zero Collisions Detected — Ready to Publish
                      </h3>
                      <p className="text-xs text-emerald-700 dark:text-emerald-300 mt-1">
                        All professor schedules, room capacities, lunch breaks, and student group continuous lab sessions satisfy all institutional constraints.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="p-5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h3 className="font-bold text-sm text-rose-900 dark:text-rose-200">
                        {sweepResult?.total_conflicts || 0} Conflict(s) Detected
                      </h3>
                      <p className="text-xs text-rose-700 dark:text-rose-300 mt-1">
                        The schedule cannot be published until coordinators resolve these clashes.
                      </p>

                      <div className="mt-3 space-y-1.5 max-h-48 overflow-y-auto">
                        {sweepResult?.conflicts?.map((c, i) => (
                          <div key={i} className="text-[11px] p-2 rounded bg-white dark:bg-slate-900 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300">
                            <strong>{c.type}:</strong> {c.message} {c.course_code ? `(${c.course_code})` : ''}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Action Controls */}
                <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
                  <button
                    onClick={() => {
                      const reason = prompt('Specify adjustment feedback for branch coordinator:');
                      if (reason !== null) {
                        sendBackMutation.mutate({ id: activeVersion.id, reason });
                      }
                    }}
                    className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-200 transition-colors"
                  >
                    Send Back to Draft
                  </button>

                  <button
                    disabled={!sweepResult?.valid || publishMutation.isPending}
                    onClick={() => {
                      if (confirm(`Officially PUBLISH ${activeVersion.name}?`)) {
                        publishMutation.mutate(activeVersion.id);
                      }
                    }}
                    className={`px-5 py-2.5 text-xs font-bold rounded-lg text-white shadow-sm transition-all flex items-center gap-2 ${
                      sweepResult?.valid
                        ? 'bg-emerald-600 hover:bg-emerald-700 cursor-pointer shadow-emerald-500/20'
                        : 'bg-slate-300 dark:bg-slate-800 cursor-not-allowed opacity-60'
                    }`}
                  >
                    <ShieldCheck className="w-4 h-4" />
                    <span>{publishMutation.isPending ? 'Publishing...' : 'Approve & Publish Timetable'}</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
