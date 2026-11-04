import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Calendar,
  Printer,
  Sparkles,
  BookOpen,
  DoorOpen,
  Coffee,
  AlertCircle,
  Clock,
  UserCheck,
  Building2,
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

export const MyTimetablePage: React.FC = () => {
  const [selectedTermId, setSelectedTermId] = useState<number | undefined>();

  const { data: terms = [] } = useQuery({
    queryKey: ['academic-terms'],
    queryFn: () => academicsService.getAcademicTerms(),
  });

  const activeTerm = terms.find((t) => t.id === selectedTermId) || terms[0];

  const { data: timetable, isLoading } = useQuery({
    queryKey: ['my-timetable', activeTerm?.id],
    queryFn: () => timetableService.getMyTimetable(activeTerm?.id),
    enabled: !!activeTerm,
  });

  // Slot lookup map
  const meetingsMap = React.useMemo(() => {
    const map = new Map<string, ScheduledMeeting>();
    if (!timetable?.meetings) return map;
    timetable.meetings.forEach((m) => {
      for (let s = m.start_slot; s <= m.end_slot; s++) {
        map.set(`${m.weekday}-${s}`, m);
      }
    });
    return map;
  }, [timetable]);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 print:space-y-3">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 print:hidden">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-300 mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Faculty Personal Schedule</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">My Weekly Timetable</h1>
          <p className="text-sm text-slate-500">
            Official published timetable for {timetable?.professor_name || 'Faculty Member'}.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={activeTerm?.id || ''}
            onChange={(e) => setSelectedTermId(Number(e.target.value))}
            className="px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 font-medium"
          >
            {terms.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>

          <button
            onClick={handlePrint}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-primary-600 hover:bg-primary-700 text-white shadow-sm transition-colors flex items-center gap-2"
          >
            <Printer className="w-4 h-4" />
            <span>Print Timetable</span>
          </button>
        </div>
      </div>

      {/* Print Only Header */}
      <div className="hidden print:block text-center border-b pb-4 mb-4">
        <h1 className="text-xl font-bold">{timetable?.professor_name} — Teaching Timetable</h1>
        <p className="text-sm text-slate-600">{activeTerm?.name} • Published University Timetable</p>
      </div>

      {/* Status & Summary Bar */}
      <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-wrap items-center justify-between gap-4 print:border-none print:p-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary-50 dark:bg-primary-950 flex items-center justify-center text-primary-600">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">
              {timetable?.professor_name || 'Loading Professor...'}
            </h2>
            <p className="text-xs text-slate-500 font-mono">
              {timetable?.meetings?.length || 0} Teaching Sessions Scheduled
            </p>
          </div>
        </div>

        {timetable?.status && (
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold ${
              timetable.status === 'PUBLISHED'
                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
            }`}
          >
            {timetable.status} SCHEDULE
          </span>
        )}
      </div>

      {/* Weekly Grid */}
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
                      const isUnavail = timetable?.unavailability?.some(
                        (u) =>
                          (u.weekday === day.id || u.weekday === null) &&
                          slot.no >= u.start_slot &&
                          slot.no <= u.end_slot
                      );

                      return (
                        <td
                          key={day.id}
                          className={`p-2 border border-slate-200 dark:border-slate-800 h-20 align-top ${
                            isUnavail
                              ? 'bg-slate-100/70 dark:bg-slate-800/50'
                              : 'bg-white dark:bg-slate-900'
                          }`}
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
                                    {meeting.course_type}
                                  </span>
                                </div>
                                <p className="truncate font-semibold mt-0.5">{meeting.course_name}</p>
                              </div>

                              <div className="pt-1.5 border-t border-black/5 dark:border-white/5 flex items-center justify-between text-[10px]">
                                <span className="font-bold">
                                  {meeting.building_code} - Rm {meeting.room_no}
                                </span>
                                <span className="font-mono opacity-80">
                                  {meeting.cohort_str?.split(' - ')[0] || meeting.branch_code}
                                </span>
                              </div>
                            </div>
                          ) : isUnavail ? (
                            <div className="h-full flex items-center justify-center text-[10px] text-slate-400 font-medium">
                              Unavailable Block
                            </div>
                          ) : null}
                        </td>
                      );
                    })}
                  </tr>

                  {isLunchBreakSlot && (
                    <tr className="bg-amber-50/70 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 text-center text-[11px] font-semibold print:bg-slate-100">
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

      {/* Holidays Notice */}
      {timetable?.holidays && timetable.holidays.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 print:hidden">
          <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider mb-2">
            Academic Holidays for {activeTerm?.name}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            {timetable.holidays.map((h) => (
              <div key={h.id} className="p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                <span className="font-bold block text-primary-600">{h.date}</span>
                <span className="text-slate-600 dark:text-slate-300">{h.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
