import React, { useState } from 'react';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import {
  Calendar,
  Printer,
  CalendarCog,
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
import { pickCurrentTerm, formatTermName } from '../utils/terms';
import { useAuth } from '../hooks/useAuth';

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
  const { user } = useAuth();
  const profile = user?.professor_profile;

  const [selectedTermId, setSelectedTermId] = useState<number | undefined>();
  const [selectedVersionId, setSelectedVersionId] = useState<number | undefined>();

  const { data: terms = [] } = useQuery({
    queryKey: ['academic-terms'],
    queryFn: () => academicsService.getAcademicTerms(),
  });

  const activeTerm = terms.find((t) => t.id === selectedTermId) || pickCurrentTerm(terms);

  const { data: timetable, isLoading } = useQuery({
    queryKey: ['my-timetable', activeTerm?.id, selectedVersionId],
    placeholderData: keepPreviousData,
    queryFn: () => timetableService.getMyTimetable(activeTerm?.id, selectedVersionId),
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

  const totalSessions = timetable?.meetings?.length || 0;
  const totalContactHours = React.useMemo(() => {
    if (!timetable?.meetings) return 0;
    return timetable.meetings.reduce((sum, m) => sum + (m.duration_slots || 1), 0);
  }, [timetable]);

  const uniqueCourses = React.useMemo(() => {
    if (!timetable?.meetings) return [];
    const map = new Map<
      string,
      {
        code: string;
        name: string;
        type: string;
        cohort: string;
        room: string;
        weeklyMeetings: number;
        totalHours: number;
      }
    >();

    timetable.meetings.forEach((m) => {
      const key = `${m.course_code}-${m.cohort_str || m.branch_code}`;
      const existing = map.get(key);
      const hours = m.duration_slots || 1;
      if (existing) {
        existing.weeklyMeetings += 1;
        existing.totalHours += hours;
      } else {
        map.set(key, {
          code: m.course_code || 'COURSE',
          name: m.course_name || 'Subject',
          type: m.course_type || 'THEORY',
          cohort: m.cohort_str?.split(' - ')[0] || m.branch_code || 'General',
          room: `Rm ${m.room_no || 'TBD'} (${m.building_code || 'Main'})`,
          weeklyMeetings: 1,
          totalHours: hours,
        });
      }
    });

    return Array.from(map.values());
  }, [timetable]);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 print:space-y-3">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 print:hidden">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">My Weekly Timetable</h1>
          <p className="text-sm text-slate-500 mt-1">
            Official published timetable for {timetable?.professor_name || 'Faculty Member'}.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={activeTerm?.id || ''}
            onChange={(e) => {
              setSelectedTermId(Number(e.target.value));
              setSelectedVersionId(undefined);
            }}
            className="px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 font-medium"
          >
            {terms.map((t) => (
              <option key={t.id} value={t.id}>
                {formatTermName(t.name)}
              </option>
            ))}
          </select>

          {timetable?.available_versions && timetable.available_versions.filter((v) => v.status === 'PUBLISHED').length > 1 && (
            <select
              value={selectedVersionId || timetable.schedule_version_id || ''}
              onChange={(e) => setSelectedVersionId(Number(e.target.value))}
              className="px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 font-medium text-slate-700 dark:text-slate-300"
            >
              {timetable.available_versions
                .filter((v) => v.status === 'PUBLISHED')
                .map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name || `Version ${v.version_no}`}
                  </option>
                ))}
            </select>
          )}

          <button
            onClick={handlePrint}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-primary-600 hover:bg-primary-700 text-white transition-colors flex items-center gap-2"
          >
            <Printer className="w-4 h-4" />
            <span>Print Timetable</span>
          </button>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* Formal Academic Masthead (Visible ONLY during print/PDF export) */}
      {/* ------------------------------------------------------------- */}
      <div className="hidden print:block bg-white text-black border-b-2 border-black pb-2 mb-2">
        {/* Top Header Institution and Document Title */}
        <div className="flex items-start justify-between pb-1.5 border-b-2 border-black">
          <div>
            <h1 className="text-lg font-black tracking-tight text-black uppercase">
              National Institute of Technology Jamshedpur
            </h1>
            <p className="text-[11px] font-black text-black tracking-wider uppercase">
              OFFICE OF THE DEAN ACADEMIC AFFAIRS • FACULTY TEACHING TIMETABLE
            </p>
          </div>
          <div className="text-right text-[10px] text-black font-mono">
            <span className="inline-block px-2 py-0.5 border-2 border-black font-black uppercase text-black bg-white rounded">
              STATUS: {timetable?.status === 'PUBLISHED' ? 'OFFICIAL PUBLISHED' : timetable?.status || 'APPROVED'}
            </span>
            <p className="mt-1 font-bold text-black">
              Generated: {new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
            </p>
            <p className="text-black font-bold">Doc ID: #SCH-FAC-{timetable?.professor_id || user?.id || '00'}-{timetable?.schedule_version_id || 'VER'}</p>
          </div>
        </div>

        {/* PROMINENT PROFESSOR IDENTIFICATION (PRINTED RIGHT ON TOP) */}
        <div className="mt-2 p-2 bg-white border-2 border-black rounded flex items-center justify-between text-black">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-black uppercase tracking-widest text-black">
                Faculty Member / Teacher:
              </span>
              {user?.employee_code && (
                <span className="text-[10px] font-mono font-black text-black px-1.5 py-0.2 border border-black rounded">
                  Emp ID: {user.employee_code}
                </span>
              )}
            </div>
            <div className="text-lg font-black text-black uppercase tracking-tight flex items-center gap-2">
              <span>{timetable?.professor_name || user?.full_name || 'Faculty Member'}</span>
              {profile?.designation && (
                <span className="text-xs font-black text-black normal-case px-2 py-0.2 border border-black rounded bg-white">
                  {profile.designation}
                </span>
              )}
            </div>
            <div className="text-[11px] font-bold text-black flex flex-wrap items-center gap-x-4 gap-y-0.5 pt-0.5">
              <span>
                Department: <span className="font-black">{profile?.department?.name || 'Department of Computer Science & Engineering'}</span>
                {profile?.department?.code && ` (${profile.department.code})`}
              </span>
              <span>
                Academic Term: <span className="font-black">{formatTermName(activeTerm?.name || timetable?.term_name) || 'Academic Term'}</span>
              </span>
            </div>
          </div>

          <div className="text-right border-l-2 border-black pl-4 space-y-0.5">
            <span className="text-[9px] font-black text-black uppercase tracking-wider block">
              Teaching Assignment Load
            </span>
            <div className="text-base font-black text-black">
              {totalSessions} Sessions
            </div>
            <div className="text-[11px] font-black text-black">
              {totalContactHours} Contact Hours / Wk
            </div>
          </div>
        </div>
      </div>

      {/* Status & Summary Bar (Screen Only) */}
      <div className="p-4 rounded-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-4 print:hidden">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-md border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center flex-shrink-0">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
                {timetable?.professor_name || 'Loading Professor...'}
              </h2>
              {timetable?.created_by && (
                <span className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                  Prepared by Super Admin: <span className="font-semibold">{timetable.created_by}</span>
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 font-mono mt-0.5">
              {totalSessions} Teaching Sessions Scheduled • {timetable?.version_name || 'Schedule Version'}
            </p>
          </div>
        </div>

        {timetable?.status && (
          <span
            className={`px-3 py-1 rounded text-xs font-semibold ${
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
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 overflow-x-auto print:border-none print:p-0 print:shadow-none print:bg-white">
        <table className="w-full min-w-[720px] print:min-w-full table-fixed border-collapse border border-slate-200 dark:border-slate-800 print:border-2 print:border-black text-xs print:bg-white">
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-800/60 print:bg-white text-slate-700 dark:text-slate-300 print:text-black font-black h-9 print:h-7">
              <th className="p-2 border border-slate-200 dark:border-slate-800 print:border-2 print:border-black w-28 text-left font-black print:bg-white uppercase tracking-wider text-[11px]">
                Time Slot
              </th>
              {WEEKDAYS.map((day) => (
                <th
                  key={day.id}
                  className="p-2 border border-slate-200 dark:border-slate-800 print:border-2 print:border-black text-center font-black print:bg-white uppercase tracking-wider text-[11px]"
                >
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
                  <tr className="h-[74px] print:h-[48px] print:bg-white">
                    <td className="p-2 print:p-1.5 border border-slate-200 dark:border-slate-800 print:border-2 print:border-black bg-slate-50/50 dark:bg-slate-800/30 print:bg-white text-slate-600 print:text-black font-mono text-[11px] align-top">
                      <div className="font-black text-slate-800 dark:text-slate-200 print:text-black text-[11px] leading-tight">
                        Slot {slot.no}
                      </div>
                      <div className="text-[10px] text-slate-400 print:text-black font-bold mt-0.5 leading-tight">
                        {slot.time}
                      </div>
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
                          className={`p-1.5 print:p-1 border border-slate-200 dark:border-slate-800 print:border-2 print:border-black h-[74px] print:h-[48px] align-top ${
                            isUnavail
                              ? 'bg-slate-100/70 dark:bg-slate-800/50 print:bg-white'
                              : 'bg-white dark:bg-slate-900 print:bg-white'
                          }`}
                        >
                          {meeting ? (
                            <div
                              className={`p-1.5 print:p-1 rounded border text-[11px] h-full flex flex-col justify-between overflow-hidden print:bg-white print:border-2 print:border-black ${
                                meeting.course_type === 'LAB'
                                  ? 'bg-purple-50 dark:bg-purple-950/40 border-purple-200 dark:border-purple-800/60 text-purple-950 dark:text-purple-200 print:text-black'
                                  : 'bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-800/60 text-blue-950 dark:text-blue-200 print:text-black'
                              }`}
                            >
                              <div>
                                <div className="flex items-center justify-between gap-1 min-w-0 font-black">
                                  <span className="font-mono flex-shrink-0 text-slate-900 dark:text-white print:text-black text-[11px] font-black">
                                    {meeting.course_code}
                                  </span>
                                  <span className="text-[9px] px-1 py-0.2 rounded whitespace-nowrap truncate min-w-0 font-black bg-white/80 dark:bg-black/40 print:bg-white print:border print:border-black print:text-black">
                                    {meeting.course_type}
                                  </span>
                                </div>
                                <p className="truncate font-black mt-0.5 text-slate-800 dark:text-slate-200 print:text-black text-[10px] leading-tight">
                                  {meeting.course_name}
                                </p>
                              </div>

                              <div className="pt-0.5 border-t border-black/5 dark:border-white/5 print:border-t print:border-black flex items-center justify-between text-[10px] print:text-[9px] font-black leading-none">
                                <span className="font-black text-slate-800 dark:text-slate-200 print:text-black">
                                  Rm {meeting.room_no} ({meeting.building_code})
                                </span>
                                <span className="font-mono font-black text-slate-600 dark:text-slate-400 print:text-black">
                                  {meeting.cohort_str?.split(' - ')[0] || meeting.branch_code}
                                </span>
                              </div>
                            </div>
                          ) : isUnavail ? (
                            <div className="h-full flex items-center justify-center text-[10px] text-slate-500 print:text-black font-black font-mono text-center print:bg-white">
                              UNAVAILABLE
                            </div>
                          ) : (
                            <div className="h-full flex items-center justify-center text-slate-200 dark:text-slate-700 print:text-black text-[10px] font-black font-mono select-none print:bg-white">
                              —
                            </div>
                          )}
                        </td>
                      );
                    })}
                  </tr>

                  {isLunchBreakSlot && (
                    <tr className="bg-amber-50/70 dark:bg-amber-950/30 print:bg-white text-amber-800 dark:text-amber-300 print:text-black text-center text-[11px] font-black h-7 print:h-6 border border-slate-200 dark:border-slate-800 print:border-2 print:border-black">
                      <td className="p-1 border border-slate-200 dark:border-slate-800 print:border-2 print:border-black font-mono font-black whitespace-nowrap print:bg-white print:text-black">
                        <Coffee className="w-3.5 h-3.5 inline-block align-[-2px] mr-1 print:hidden" />12:30–14:00
                      </td>
                      <td colSpan={5} className="p-1 border border-slate-200 dark:border-slate-800 print:border-2 print:border-black print:bg-white font-black uppercase tracking-wider text-[11px] print:text-black">
                        Mandatory University Lunch Break (12:30 – 14:00)
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* Official Signatures & Certification Block (Single-Page Fit) */}
      {/* ------------------------------------------------------------- */}
      <div className="hidden print:block mt-3 pt-2 border-t-2 border-black bg-white">
        <div className="grid grid-cols-3 gap-6 text-center text-black">
          <div>
            <div className="border-b-2 border-black w-48 mx-auto mb-1 h-5"></div>
            <p className="font-black text-xs text-black">{timetable?.professor_name || user?.full_name}</p>
            <p className="text-[10px] font-bold uppercase text-black">Faculty Signature</p>
          </div>
          <div>
            <div className="border-b-2 border-black w-48 mx-auto mb-1 h-5"></div>
            <p className="font-black text-xs text-black">Head of Department (HOD)</p>
            <p className="text-[10px] font-bold uppercase text-black">{profile?.department?.name || 'Department Seal'}</p>
          </div>
          <div>
            <div className="border-b-2 border-black w-48 mx-auto mb-1 h-5"></div>
            <p className="font-black text-xs text-black">Dean (Academic Affairs)</p>
            <p className="text-[10px] font-bold uppercase text-black">Approved & Verified</p>
          </div>
        </div>
        <p className="text-[9px] font-bold text-black text-center mt-2 font-mono uppercase tracking-wider">
          Official Academic Schedule • National Institute of Technology Jamshedpur • Smart Timetable System
        </p>
      </div>

      {/* Holidays Notice */}
      {timetable?.holidays && timetable.holidays.length > 0 && (
        <div className="p-4 rounded-md bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 print:hidden">
          <h3 className="text-xs font-semibold text-slate-800 dark:text-slate-200 uppercase tracking-wider mb-2">
            Academic Holidays for {activeTerm?.name}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            {timetable.holidays.map((h) => (
              <div key={h.id} className="p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                <span className="font-semibold block text-primary-600">{h.date}</span>
                <span className="text-slate-600 dark:text-slate-300">{h.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
