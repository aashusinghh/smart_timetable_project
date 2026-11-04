import React, { useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  GitBranch,
  Calendar,
  Coffee,
  Printer,
  Sparkles,
  Users,
  BookOpen,
} from 'lucide-react';
import { timetableService } from '../services/timetable';
import { academicsService } from '../services/academics';
import { ScheduledMeeting } from '../types';

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

export const BranchTimetablePage: React.FC = () => {
  const { id: paramBranchId } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();

  const [selectedBranchId, setSelectedBranchId] = useState<number | undefined>(
    paramBranchId ? Number(paramBranchId) : undefined
  );
  const [selectedTermId, setSelectedTermId] = useState<number | undefined>();
  const [selectedSemester, setSelectedSemester] = useState<number | undefined>(3);

  const { data: branches = [] } = useQuery({
    queryKey: ['branches'],
    queryFn: () => academicsService.getBranches(),
  });

  const activeBranch = branches.find((b) => b.id === selectedBranchId) || branches[0];

  const { data: terms = [] } = useQuery({
    queryKey: ['academic-terms'],
    queryFn: () => academicsService.getAcademicTerms(),
  });

  const activeTerm = terms.find((t) => t.id === selectedTermId) || terms[0];

  const { data: branchTimetable, isLoading } = useQuery({
    queryKey: ['branch-timetable', activeBranch?.id, activeTerm?.id, selectedSemester],
    queryFn: () =>
      activeBranch
        ? timetableService.getBranchTimetable(activeBranch.id, {
            term_id: activeTerm?.id,
            semester_no: selectedSemester,
          })
        : Promise.resolve({ branch_id: 0, branch_code: '', branch_name: '', meetings: [] }),
    enabled: !!activeBranch,
  });

  // Map meetings
  const meetingsMap = React.useMemo(() => {
    const map = new Map<string, ScheduledMeeting>();
    if (!branchTimetable?.meetings) return map;
    branchTimetable.meetings.forEach((m) => {
      for (let s = m.start_slot; s <= m.end_slot; s++) {
        map.set(`${m.weekday}-${s}`, m);
      }
    });
    return map;
  }, [branchTimetable]);

  return (
    <div className="space-y-6 print:space-y-3">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 print:hidden">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 dark:bg-blue-950/70 text-blue-700 dark:text-blue-300 mb-2">
            <GitBranch className="w-3.5 h-3.5" />
            <span>Branch Public Schedule Viewer</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            {activeBranch ? `${activeBranch.name} (${activeBranch.code})` : 'Branch Timetable'}
          </h1>
          <p className="text-sm text-slate-500">
            Read-only master timetable view for students and faculty.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={activeBranch?.id || ''}
            onChange={(e) => setSelectedBranchId(Number(e.target.value))}
            className="px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 font-bold"
          >
            {branches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name} ({b.code})
              </option>
            ))}
          </select>

          <select
            value={selectedSemester || ''}
            onChange={(e) => setSelectedSemester(Number(e.target.value))}
            className="px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 font-medium"
          >
            {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
              <option key={s} value={s}>
                Semester {s}
              </option>
            ))}
          </select>

          <button
            onClick={() => window.print()}
            className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-primary-600 hover:bg-primary-700 text-white flex items-center gap-1.5"
          >
            <Printer className="w-4 h-4" />
            <span>Print</span>
          </button>
        </div>
      </div>

      {/* Grid */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm overflow-x-auto print:border-none print:p-0">
        <table className="w-full border-collapse border border-slate-200 dark:border-slate-800 text-xs">
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-800/60 text-slate-700 dark:text-slate-300 font-bold">
              <th className="p-3 border border-slate-200 dark:border-slate-800 w-32 text-left">Time Slot</th>
              {WEEKDAYS.map((day) => (
                <th key={day.id} className="p-3 border border-slate-200 dark:border-slate-800 text-center">
                  {day.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SLOTS.map((slot) => {
              const isLunchBreakSlot = slot.no === 4;
              return (
                <React.Fragment key={slot.no}>
                  <tr>
                    <td className="p-2.5 border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 text-slate-500 font-mono text-[11px]">
                      <div className="font-bold text-slate-800 dark:text-slate-200">Slot {slot.no}</div>
                      <div className="text-[10px] text-slate-400">{slot.time}</div>
                    </td>

                    {WEEKDAYS.map((day) => {
                      const meeting = meetingsMap.get(`${day.id}-${slot.no}`);
                      return (
                        <td
                          key={day.id}
                          className="p-2 border border-slate-200 dark:border-slate-800 h-20 align-top bg-white dark:bg-slate-900"
                        >
                          {meeting ? (
                            <div
                              className={`p-2 rounded-lg border text-[11px] shadow-sm h-full flex flex-col justify-between ${
                                meeting.course_type === 'LAB'
                                  ? 'bg-purple-50 dark:bg-purple-950/40 border-purple-200 dark:border-purple-800/60 text-purple-950 dark:text-purple-200'
                                  : 'bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-800/60 text-blue-950 dark:text-blue-200'
                              }`}
                            >
                              <div>
                                <div className="flex items-center justify-between font-bold">
                                  <span className="font-mono">{meeting.course_code}</span>
                                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/70 dark:bg-black/30">
                                    Room {meeting.room_no}
                                  </span>
                                </div>
                                <p className="truncate font-semibold mt-0.5">{meeting.course_name}</p>
                              </div>

                              <div className="pt-1.5 border-t border-black/5 dark:border-white/5 flex items-center justify-between text-[10px] opacity-80">
                                <span className="truncate">{meeting.professor_name}</span>
                                {meeting.group_codes && meeting.group_codes.length > 0 && (
                                  <span className="font-mono font-bold">[{meeting.group_codes.join(', ')}]</span>
                                )}
                              </div>
                            </div>
                          ) : null}
                        </td>
                      );
                    })}
                  </tr>

                  {isLunchBreakSlot && (
                    <tr className="bg-amber-50/70 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 text-center text-[11px] font-semibold">
                      <td className="p-2 border border-slate-200 dark:border-slate-800 flex items-center justify-center gap-1 font-mono">
                        <Coffee className="w-3.5 h-3.5" /> 12:30–14:00
                      </td>
                      <td colSpan={5} className="p-2 border border-slate-200 dark:border-slate-800">
                        ☕ University Lunch Break
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
  );
};
