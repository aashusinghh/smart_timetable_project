import React, { useState } from 'react';
import {
  Sparkles,
  X,
  Clock,
  Layers,
  AlertTriangle,
  RotateCcw,
  CheckSquare,
  Square,
} from 'lucide-react';
import { Branch } from '../../types';

interface AutoGenerateModalProps {
  isOpen: boolean;
  onClose: () => void;
  branches: Branch[];
  onStartGeneration: (config: {
    branch_ids: number[];
    time_limit: number;
    replace_existing: boolean;
  }) => void;
  isLoading?: boolean;
}

export const AutoGenerateModal: React.FC<AutoGenerateModalProps> = ({
  isOpen,
  onClose,
  branches,
  onStartGeneration,
  isLoading = false,
}) => {
  const [selectedBranchIds, setSelectedBranchIds] = useState<number[]>(
    branches.map((b) => b.id)
  );
  const [timeLimit, setTimeLimit] = useState<number>(60);
  const [replaceExisting, setReplaceExisting] = useState<boolean>(true);
  const [validationError, setValidationError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleToggleBranch = (id: number) => {
    setSelectedBranchIds((prev) =>
      prev.includes(id) ? prev.filter((bId) => bId !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedBranchIds.length === branches.length) {
      setSelectedBranchIds([]);
    } else {
      setSelectedBranchIds(branches.map((b) => b.id));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedBranchIds.length === 0) {
      setValidationError('Please select at least one branch for auto-scheduling.');
      return;
    }
    setValidationError(null);
    onStartGeneration({
      branch_ids: selectedBranchIds,
      time_limit: timeLimit,
      replace_existing: replaceExisting,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-xl overflow-hidden animate-scale-up">
        {/* Header */}
        <div className="px-6 py-5 bg-gradient-to-r from-primary-600 via-primary-700 to-indigo-700 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-white/15 rounded-xl backdrop-blur-md">
              <Sparkles className="w-6 h-6 text-amber-300" />
            </div>
            <div>
              <h3 className="text-xl font-bold">Smart Auto-Scheduling</h3>
              <p className="text-xs text-white/80 mt-0.5">
                Generate clash-free timetable using Google OR-Tools CP-SAT
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {validationError && (
            <div className="p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-xl flex items-center gap-2.5 text-sm text-red-700 dark:text-red-300">
              <AlertTriangle className="w-4 h-4 shrink-0 text-red-600" />
              <span>{validationError}</span>
            </div>
          )}

          {/* Branch Selection */}
          <div>
            <div className="flex items-center justify-between mb-2.5">
              <label className="text-sm font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                <Layers className="w-4 h-4 text-primary-500" />
                Target Academic Branches
              </label>
              <button
                type="button"
                onClick={handleSelectAll}
                className="text-xs font-medium text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1"
              >
                {selectedBranchIds.length === branches.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            <div className="max-h-44 overflow-y-auto border border-slate-200 dark:border-slate-800 rounded-xl p-2.5 space-y-1 bg-slate-50/50 dark:bg-slate-950/30">
              {branches.length === 0 ? (
                <p className="text-xs text-slate-500 py-3 text-center">No branches available for this term.</p>
              ) : (
                branches.map((b) => {
                  const isChecked = selectedBranchIds.includes(b.id);
                  return (
                    <div
                      key={b.id}
                      onClick={() => handleToggleBranch(b.id)}
                      className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${
                        isChecked
                          ? 'bg-primary-50 dark:bg-primary-950/40 border border-primary-200 dark:border-primary-800 text-primary-900 dark:text-primary-100'
                          : 'hover:bg-slate-100 dark:hover:bg-slate-800/60 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 text-sm">
                        {isChecked ? (
                          <CheckSquare className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                        ) : (
                          <Square className="w-4 h-4 text-slate-400" />
                        )}
                        <span className="font-medium">{b.code}</span>
                        <span className="text-xs text-slate-500 dark:text-slate-400">({b.name})</span>
                      </div>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                        {b.degree_name}
                      </span>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Solver Time Limit */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                <Clock className="w-4 h-4 text-primary-500" />
                Solver Time Limit: <span className="text-primary-600 dark:text-primary-400 font-bold">{timeLimit}s</span>
              </label>
              <span className="text-xs text-slate-500">Default: 60s (10s – 300s)</span>
            </div>
            <input
              type="range"
              min="10"
              max="180"
              step="5"
              value={timeLimit}
              onChange={(e) => setTimeLimit(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-primary-600"
            />
            <div className="flex justify-between text-[11px] text-slate-400 mt-1">
              <span>10s (Fast preview)</span>
              <span>60s (Recommended)</span>
              <span>180s (Deep search)</span>
            </div>
          </div>

          {/* Replace Existing Option */}
          <div className="p-3.5 border border-amber-200 dark:border-amber-900/60 bg-amber-50/50 dark:bg-amber-950/20 rounded-xl">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={replaceExisting}
                onChange={(e) => setReplaceExisting(e.target.checked)}
                className="mt-0.5 rounded border-amber-400 text-amber-600 focus:ring-amber-500 dark:bg-slate-900 w-4 h-4"
              />
              <div className="text-xs text-slate-700 dark:text-slate-300">
                <span className="font-semibold text-amber-900 dark:text-amber-300 block mb-0.5">
                  Replace Existing Timetable for Selected Branches
                </span>
                When checked, existing meetings in the selected branches will be replaced upon proposal commit.
                Meetings in unselected branches remain strictly preserved.
              </div>
            </label>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-700 hover:to-indigo-700 rounded-xl shadow-lg shadow-primary-500/25 flex items-center gap-2 transition-all disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4 text-amber-300" />
              {isLoading ? 'Starting Generator...' : 'Start Auto-Scheduling'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

