import React, { useState, useMemo } from 'react';
import {
  X,
  Sparkles,
  Check,
  Trash2,
  Filter,
  Calendar,
  Layers,
  Award,
  AlertTriangle,
  Building,
  User,
  Clock,
  ShieldCheck,
  BarChart3,
  List,
} from 'lucide-react';
import { AutoScheduleProposal, ProposedMeeting } from '../../types';
import { ScoringDashboard } from './ScoringDashboard';

interface ProposalPreviewModalProps {
  isOpen: boolean;
  proposal: AutoScheduleProposal | null;
  onClose: () => void;
  onCommit: (proposalId: number) => void;
  onDiscard: (proposalId: number) => void;
  isCommitting?: boolean;
  isDiscarding?: boolean;
}

const WEEKDAYS = [
  { id: 1, name: 'Monday', short: 'Mon' },
  { id: 2, name: 'Tuesday', short: 'Tue' },
  { id: 3, name: 'Wednesday', short: 'Wed' },
  { id: 4, name: 'Thursday', short: 'Thu' },
  { id: 5, name: 'Friday', short: 'Fri' },
];

const SLOTS = [
  { no: 1, time: '08:30 - 09:30', session: 'MORNING' },
  { no: 2, time: '09:30 - 10:30', session: 'MORNING' },
  { no: 3, time: '10:30 - 11:30', session: 'MORNING' },
  { no: 4, time: '11:30 - 12:30', session: 'MORNING' },
  { no: 5, time: '14:00 - 15:00', session: 'AFTERNOON' },
  { no: 6, time: '15:00 - 16:00', session: 'AFTERNOON' },
  { no: 7, time: '16:00 - 17:00', session: 'AFTERNOON' },
  { no: 8, time: '17:00 - 18:00', session: 'AFTERNOON' },
];

export const ProposalPreviewModal: React.FC<ProposalPreviewModalProps> = ({
  isOpen,
  proposal,
  onClose,
  onCommit,
  onDiscard,
  isCommitting = false,
  isDiscarding = false,
}) => {
  const [activeTab, setActiveTab] = useState<'grid' | 'scoring' | 'list'>('grid');
  const [selectedCohortId, setSelectedCohortId] = useState<number | 'ALL'>('ALL');
  const [showCommitConfirm, setShowCommitConfirm] = useState(false);

  if (!isOpen || !proposal) return null;

  // Extract distinct cohorts from proposed meetings
  const cohorts = useMemo(() => {
    const map = new Map<number, string>();
    proposal.proposed_meetings.forEach((m) => {
      if (m.cohort_id) {
        map.set(m.cohort_id, m.cohort_name || `Cohort #${m.cohort_id}`);
      }
    });
    return Array.from(map.entries()).map(([id, name]) => ({ id, name }));
  }, [proposal]);

  // Filter meetings by selected cohort
  const filteredMeetings = useMemo(() => {
    if (selectedCohortId === 'ALL') {
      return proposal.proposed_meetings;
    }
    return proposal.proposed_meetings.filter((m) => m.cohort_id === selectedCohortId);
  }, [proposal, selectedCohortId]);

  // Index meetings by (weekday, slot)
  const meetingsBySlot = useMemo(() => {
    const map = new Map<string, ProposedMeeting[]>();
    filteredMeetings.forEach((m) => {
      for (let s = m.start_slot; s < m.start_slot + m.duration_slots; s++) {
        const key = `${m.weekday}-${s}`;
        const existing = map.get(key) || [];
        existing.push(m);
        map.set(key, existing);
      }
    });
    return map;
  }, [filteredMeetings]);

  const replaceExisting = proposal.generation_metadata?.replace_existing ?? false;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fade-in">
      <div className="bg-slate-50 dark:bg-slate-900 rounded-3xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-7xl h-[92vh] flex flex-col overflow-hidden animate-scale-up">
        {/* Top Header */}
        <div className="px-6 py-4 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-4">
            <div className="p-2.5 bg-gradient-to-tr from-primary-600 to-indigo-600 rounded-2xl text-white shadow-md shadow-primary-500/25">
              <Sparkles className="w-6 h-6 text-amber-300" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  Auto-Schedule Proposal Preview
                </h3>
                <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-primary-100 dark:bg-primary-950/60 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-800">
                  Proposal #{proposal.id}
                </span>
                <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                  proposal.solver_status === 'OPTIMAL' || proposal.solver_status === 'FEASIBLE'
                    ? 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                    : 'bg-red-100 text-red-700'
                }`}>
                  {proposal.solver_status}
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 flex items-center gap-3">
                <span>Total Meetings Placed: <b className="text-slate-700 dark:text-slate-200">{proposal.proposed_meetings.length}</b></span>
                <span>•</span>
                <span>Quality Score: <b className="text-primary-600 dark:text-primary-400 font-bold">{proposal.quality_score.toFixed(1)} / 100</b></span>
                <span>•</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  0 Hard-Constraint Clashes
                </span>
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2">
            <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs font-semibold">
              <button
                onClick={() => setActiveTab('grid')}
                className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                  activeTab === 'grid'
                    ? 'bg-white dark:bg-slate-700 text-primary-600 dark:text-primary-300 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                <Calendar className="w-3.5 h-3.5" />
                Timetable Grid
              </button>
              <button
                onClick={() => setActiveTab('scoring')}
                className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                  activeTab === 'scoring'
                    ? 'bg-white dark:bg-slate-700 text-primary-600 dark:text-primary-300 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5" />
                Scoring Breakdown
              </button>
              <button
                onClick={() => setActiveTab('list')}
                className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                  activeTab === 'list'
                    ? 'bg-white dark:bg-slate-700 text-primary-600 dark:text-primary-300 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                <List className="w-3.5 h-3.5" />
                Meetings List ({proposal.proposed_meetings.length})
              </button>
            </div>

            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'grid' && (
            <div className="space-y-4">
              {/* Cohort Selector */}
              <div className="flex items-center justify-between bg-white dark:bg-slate-900 p-3 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                <div className="flex items-center gap-3">
                  <Filter className="w-4 h-4 text-primary-500" />
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Cohort View:
                  </span>
                  <select
                    value={selectedCohortId}
                    onChange={(e) => setSelectedCohortId(e.target.value === 'ALL' ? 'ALL' : Number(e.target.value))}
                    className="text-xs font-semibold bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-1.5 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="ALL">All Cohorts ({proposal.proposed_meetings.length} meetings)</option>
                    {cohorts.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="text-xs text-slate-500 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
                  <span>Read-only candidate preview — Live timetable remains untouched</span>
                </div>
              </div>

              {/* Weekly Timetable Grid */}
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-x-auto shadow-sm">
                <table className="w-full border-collapse min-w-[850px]">
                  <thead>
                    <tr className="bg-slate-100/70 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800">
                      <th className="p-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider w-28">
                        Time Slot
                      </th>
                      {WEEKDAYS.map((day) => (
                        <th key={day.id} className="p-3 text-center text-xs font-bold text-slate-700 dark:text-slate-200 uppercase tracking-wider">
                          {day.name}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                    {SLOTS.map((slot) => {
                      const isLunchAfter = slot.no === 4;
                      return (
                        <React.Fragment key={slot.no}>
                          <tr className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                            <td className="p-3 bg-slate-50/50 dark:bg-slate-800/40 border-r border-slate-200 dark:border-slate-800">
                              <span className="font-bold text-slate-800 dark:text-slate-200 block">Slot {slot.no}</span>
                              <span className="text-[11px] text-slate-400 block">{slot.time}</span>
                            </td>
                            {WEEKDAYS.map((day) => {
                              const key = `${day.id}-${slot.no}`;
                              const cellMeetings = meetingsBySlot.get(key) || [];

                              return (
                                <td key={day.id} className="p-2 border-r border-slate-100 dark:border-slate-800/60 align-top min-h-[70px]">
                                  {cellMeetings.length > 0 ? (
                                    <div className="space-y-1.5">
                                      {cellMeetings.map((m, idx) => {
                                        const isLab = m.duration_slots === 3;
                                        const isStart = m.start_slot === slot.no;

                                        return (
                                          <div
                                            key={idx}
                                            className={`p-2 rounded-xl border text-left shadow-xs transition-all ${
                                              isLab
                                                ? 'bg-purple-50 dark:bg-purple-950/40 border-purple-200 dark:border-purple-800 text-purple-900 dark:text-purple-100'
                                                : 'bg-primary-50 dark:bg-primary-950/40 border-primary-200 dark:border-primary-800 text-primary-900 dark:text-primary-100'
                                            }`}
                                          >
                                            <div className="flex items-center justify-between mb-1">
                                              <span className="font-bold text-xs">{m.course_code}</span>
                                              {isLab && (
                                                <span className="text-[10px] px-1.5 py-0.2 rounded-md bg-purple-200 dark:bg-purple-800 text-purple-800 dark:text-purple-200 font-bold">
                                                  3h Lab
                                                </span>
                                              )}
                                            </div>
                                            <p className="text-[11px] font-medium truncate">{m.course_name}</p>
                                            <div className="mt-1 flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400">
                                              <span className="flex items-center gap-1">
                                                <User className="w-3 h-3 text-slate-400" />
                                                {m.professor_name}
                                              </span>
                                              <span className="flex items-center gap-1 font-semibold text-slate-700 dark:text-slate-300">
                                                <Building className="w-3 h-3" />
                                                {m.building_code}-{m.room_no}
                                              </span>
                                            </div>
                                            {selectedCohortId === 'ALL' && (
                                              <span className="block mt-1 text-[9px] text-slate-400 italic">
                                                {m.cohort_name}
                                              </span>
                                            )}
                                          </div>
                                        );
                                      })}
                                    </div>
                                  ) : (
                                    <div className="h-12 flex items-center justify-center text-slate-300 dark:text-slate-700 text-[11px]">
                                      —
                                    </div>
                                  )}
                                </td>
                              );
                            })}
                          </tr>

                          {/* University Lunch Break Separator */}
                          {isLunchAfter && (
                            <tr className="bg-amber-50/70 dark:bg-amber-950/30 border-y border-amber-200 dark:border-amber-900/60">
                              <td colSpan={6} className="py-2 px-4 text-center text-xs font-semibold text-amber-800 dark:text-amber-300">
                                🍽️ University Lunch Break (12:30 – 14:00) — No classes scheduled
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'scoring' && (
            <ScoringDashboard
              overallScore={proposal.quality_score}
              breakdown={proposal.constraint_score_breakdown?.breakdown}
              metrics={proposal.constraint_score_breakdown?.metrics}
              unscheduledOfferings={proposal.unscheduled_offerings}
            />
          )}

          {activeTab === 'list' && (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 uppercase font-semibold">
                  <tr>
                    <th className="p-3">Course</th>
                    <th className="p-3">Cohort</th>
                    <th className="p-3">Professor</th>
                    <th className="p-3">Weekday</th>
                    <th className="p-3">Time Slot</th>
                    <th className="p-3">Room</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  {proposal.proposed_meetings.map((m, i) => {
                    const day = WEEKDAYS.find((d) => d.id === m.weekday)?.name || `Day ${m.weekday}`;
                    const slotInfo = SLOTS.find((s) => s.no === m.start_slot);
                    return (
                      <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                        <td className="p-3">
                          <span className="font-bold text-primary-600 dark:text-primary-400">{m.course_code}</span>
                          <span className="block text-[11px] text-slate-500">{m.course_name}</span>
                        </td>
                        <td className="p-3">{m.cohort_name}</td>
                        <td className="p-3 font-medium">{m.professor_name}</td>
                        <td className="p-3 font-semibold">{day}</td>
                        <td className="p-3">
                          Slots {m.start_slot}{m.duration_slots > 1 ? `–${m.start_slot + m.duration_slots - 1}` : ''}
                          <span className="block text-[10px] text-slate-400">({slotInfo?.time || ''})</span>
                        </td>
                        <td className="p-3">
                          <span className="font-semibold">{m.building_code}-{m.room_no}</span>
                          <span className="block text-[10px] text-slate-400 capitalize">{m.room_type?.replace('_', ' ').toLowerCase()}</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            {replaceExisting ? (
              <span className="text-amber-600 dark:text-amber-400 font-medium">
                ⚠️ Committing will replace current meetings in selected branches.
              </span>
            ) : (
              <span>Committing will append proposed meetings to current schedule version.</span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => onDiscard(proposal.id)}
              disabled={isDiscarding || isCommitting}
              className="px-4 py-2.5 text-xs font-semibold text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-xl transition-colors flex items-center gap-1.5 disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4" />
              {isDiscarding ? 'Discarding...' : 'Discard Proposal'}
            </button>

            <button
              onClick={() => setShowCommitConfirm(true)}
              disabled={isCommitting || isDiscarding}
              className="px-6 py-2.5 text-xs font-semibold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-xl shadow-lg shadow-emerald-500/25 flex items-center gap-2 transition-all disabled:opacity-50"
            >
              <Check className="w-4 h-4 text-white" />
              {isCommitting ? 'Committing...' : 'Commit Proposal to Live Timetable'}
            </button>
          </div>
        </div>

        {/* Confirmation Modal */}
        {showCommitConfirm && (
          <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 max-w-md w-full shadow-2xl text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 flex items-center justify-center mx-auto">
                <Check className="w-6 h-6" />
              </div>
              <h4 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                Confirm Timetable Commit
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                This will atomically reserve slots and write {proposal.proposed_meetings.length} meetings into the live schedule version.
                {replaceExisting && (
                  <span className="block mt-2 font-semibold text-amber-600 dark:text-amber-400">
                    Existing meetings in selected branches will be replaced.
                  </span>
                )}
              </p>
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCommitConfirm(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCommitConfirm(false);
                    onCommit(proposal.id);
                  }}
                  className="px-5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-md shadow-emerald-500/20"
                >
                  Confirm & Commit
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

