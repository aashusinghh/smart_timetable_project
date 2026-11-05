import React, { useEffect, useState } from 'react';
import {
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle,
  X,
  Cpu,
  BrainCircuit,
  Flame,
} from 'lucide-react';
import { schedulerService } from '../../services/scheduler';
import { TaskStatusResponse } from '../../types';

interface GenerationProgressModalProps {
  isOpen: boolean;
  taskId: string | null;
  onComplete: (proposalId: number) => void;
  onCancel: () => void;
}

export const GenerationProgressModal: React.FC<GenerationProgressModalProps> = ({
  isOpen,
  taskId,
  onComplete,
  onCancel,
}) => {
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !taskId) return;

    let isSubscribed = true;
    let pollInterval: NodeJS.Timeout;

    const poll = async () => {
      try {
        const data = await schedulerService.getTaskStatus(taskId);
        if (!isSubscribed) return;

        setTaskStatus(data);

        if (data.status === 'SUCCESS' && data.proposal_id) {
          // Transition smoothly to proposal preview after a brief visual confirmation
          setTimeout(() => {
            if (isSubscribed) {
              onComplete(data.proposal_id!);
            }
          }, 800);
        } else if (data.status === 'FAILURE') {
          setErrorMsg(data.error || data.message || 'Auto-scheduling engine reported a failure.');
        } else {
          pollInterval = setTimeout(poll, 1000);
        }
      } catch (err: any) {
        if (!isSubscribed) return;
        const msg = err.response?.data?.detail || 'Failed to poll task status.';
        setErrorMsg(msg);
      }
    };

    poll();

    return () => {
      isSubscribed = false;
      if (pollInterval) clearTimeout(pollInterval);
    };
  }, [isOpen, taskId, onComplete]);

  if (!isOpen) return null;

  const percentage = taskStatus?.percentage ?? 10;
  const message = taskStatus?.message || 'Optimizing timetable constraints with OR-Tools CP-SAT...';
  const isFailed = taskStatus?.status === 'FAILURE' || !!errorMsg;
  const isCompleted = taskStatus?.status === 'SUCCESS';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fade-in">
      <div className="bg-white dark:bg-slate-900 rounded-3xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-lg p-8 overflow-hidden relative text-center">
        {/* Glow effect */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-primary-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />

        {/* Top Cancel button */}
        <button
          onClick={onCancel}
          className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Status Icon */}
        <div className="mb-6 flex justify-center">
          {isFailed ? (
            <div className="w-20 h-20 rounded-2xl bg-red-100 dark:bg-red-950/60 border border-red-200 dark:border-red-800 flex items-center justify-center text-red-600 animate-scale-up">
              <AlertCircle className="w-10 h-10" />
            </div>
          ) : isCompleted ? (
            <div className="w-20 h-20 rounded-2xl bg-emerald-100 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 flex items-center justify-center text-emerald-600 animate-scale-up">
              <CheckCircle2 className="w-10 h-10" />
            </div>
          ) : (
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-primary-600 to-indigo-600 text-white flex items-center justify-center shadow-xl shadow-primary-500/30 relative">
              <BrainCircuit className="w-10 h-10 animate-pulse" />
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-amber-400 rounded-full animate-ping" />
            </div>
          )}
        </div>

        {/* Title */}
        <h3 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
          {isFailed
            ? 'Auto-Scheduling Failed'
            : isCompleted
            ? 'Schedule Proposal Ready!'
            : 'Generating Timetable...'}
        </h3>

        {/* Status Message */}
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-6 max-w-sm mx-auto min-h-[40px]">
          {isFailed ? errorMsg : message}
        </p>

        {/* Progress Bar & Percentage */}
        {!isFailed && (
          <div className="space-y-3 mb-6">
            <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-3 overflow-hidden p-0.5 border border-slate-200 dark:border-slate-700">
              <div
                className="bg-gradient-to-r from-primary-500 via-indigo-500 to-emerald-400 h-full rounded-full transition-all duration-500 ease-out shadow-sm"
                style={{ width: `${Math.min(100, Math.max(5, percentage))}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium px-1">
              <span className="flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-primary-500" />
                CP-SAT Solver Engine
              </span>
              <span className="font-bold text-primary-600 dark:text-primary-400">{percentage}%</span>
            </div>
          </div>
        )}

        {/* Step Highlights */}
        {!isFailed && !isCompleted && (
          <div className="grid grid-cols-3 gap-2 p-3 bg-slate-50 dark:bg-slate-800/40 rounded-2xl border border-slate-200/60 dark:border-slate-800 text-left mb-6 text-[11px]">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <div className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>Hard constraints</span>
            </div>
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <div className="w-2 h-2 rounded-full bg-primary-500 animate-pulse" />
              <span>Soft objectives</span>
            </div>
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <div className="w-2 h-2 rounded-full bg-indigo-500" />
              <span>Score report</span>
            </div>
          </div>
        )}

        {/* Bottom Button */}
        <div>
          {isFailed ? (
            <button
              onClick={onCancel}
              className="px-6 py-2.5 text-sm font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-xl transition-colors"
            >
              Close
            </button>
          ) : (
            <button
              onClick={onCancel}
              className="px-5 py-2 text-xs font-medium text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
            >
              Cancel Background Task
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

