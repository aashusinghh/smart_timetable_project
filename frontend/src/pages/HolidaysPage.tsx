import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Calendar as CalendarIcon,
  Plus,
  Trash2,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Coffee,
  X,
} from 'lucide-react';
import { timetableService } from '../services/timetable';
import { academicsService } from '../services/academics';
import { HolidayCalendar, DateOverride } from '../types';

export const HolidaysPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedTermId, setSelectedTermId] = useState<number | undefined>();
  const [isAddHolidayOpen, setIsAddHolidayOpen] = useState(false);
  const [newDate, setNewDate] = useState('');
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [successToast, setSuccessToast] = useState<string | null>(null);

  const { data: terms = [] } = useQuery({
    queryKey: ['academic-terms'],
    queryFn: () => academicsService.getAcademicTerms(),
  });

  const activeTerm = terms.find((t) => t.id === selectedTermId) || terms[0];

  const { data: holidays = [] } = useQuery({
    queryKey: ['holidays', activeTerm?.id],
    queryFn: () => timetableService.getHolidays(activeTerm?.id),
    enabled: !!activeTerm,
  });

  const { data: dateOverrides = [] } = useQuery({
    queryKey: ['date-overrides'],
    queryFn: () => timetableService.getDateOverrides(),
  });

  const addHolidayMutation = useMutation({
    mutationFn: (data: Partial<HolidayCalendar>) => timetableService.createHoliday(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['holidays'] });
      setIsAddHolidayOpen(false);
      setNewDate('');
      setNewName('');
      setNewDesc('');
      setSuccessToast('Academic holiday added successfully.');
      setTimeout(() => setSuccessToast(null), 3000);
    },
  });

  const deleteHolidayMutation = useMutation({
    mutationFn: (id: number) => timetableService.deleteHoliday(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['holidays'] });
      setSuccessToast('Holiday removed.');
      setTimeout(() => setSuccessToast(null), 3000);
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary-50 dark:bg-primary-950/70 text-primary-700 dark:text-primary-300 mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Academic Exceptions & Calendar</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Holidays & Class Overrides</h1>
          <p className="text-sm text-slate-500">
            Define no-teaching academic holidays and inspect single-day class cancellations and reschedules.
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
            onClick={() => setIsAddHolidayOpen(true)}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-primary-600 hover:bg-primary-700 text-white shadow-sm flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" />
            <span>Add Holiday</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Holidays List */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Academic Holidays ({holidays.length})
              </h2>
              <p className="text-xs text-slate-500">Dates where classes are suspended across the institution.</p>
            </div>
          </div>

          <div className="space-y-2.5">
            {holidays.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">No holidays defined for this academic term.</p>
            ) : (
              holidays.map((h) => (
                <div
                  key={h.id}
                  className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 flex items-center justify-between gap-3 text-xs"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary-50 dark:bg-primary-950 flex flex-col items-center justify-center text-primary-600 font-bold leading-tight">
                      <span className="text-[10px] uppercase">{new Date(h.date).toLocaleString('default', { month: 'short' })}</span>
                      <span className="text-sm font-mono">{new Date(h.date).getDate()}</span>
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900 dark:text-white">{h.name}</h3>
                      <p className="text-slate-500 font-mono text-[11px]">{h.date}</p>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      if (confirm(`Remove holiday ${h.name}?`)) {
                        deleteHolidayMutation.mutate(h.id);
                      }
                    }}
                    className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/40"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Date Overrides List */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Class Date Overrides ({dateOverrides.length})
              </h2>
              <p className="text-xs text-slate-500">Single-day cancellations and reschedules.</p>
            </div>
          </div>

          <div className="space-y-2.5">
            {dateOverrides.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">No single-day class overrides registered.</p>
            ) : (
              dateOverrides.map((ov) => (
                <div
                  key={ov.id}
                  className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-slate-900 dark:text-white">
                      {ov.meeting_course} • {ov.meeting_professor}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        ov.status === 'CANCELLED'
                          ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                          : 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                      }`}
                    >
                      {ov.status}
                    </span>
                  </div>

                  <p className="text-slate-600 dark:text-slate-400">
                    Original Date: <strong>{ov.original_date}</strong>
                    {ov.new_date && ` → Rescheduled to ${ov.new_date} (Slot ${ov.new_start_slot || 1})`}
                  </p>

                  {ov.reason && <p className="text-[11px] text-slate-500 italic">Reason: {ov.reason}</p>}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Add Holiday Modal */}
      {isAddHolidayOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-sm w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-900 dark:text-white">Add Academic Holiday</h2>
              <button onClick={() => setIsAddHolidayOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold block mb-1">Holiday Name</label>
                <input
                  type="text"
                  placeholder="e.g. Independence Day"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                />
              </div>

              <div>
                <label className="font-semibold block mb-1">Date</label>
                <input
                  type="date"
                  value={newDate}
                  onChange={(e) => setNewDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button onClick={() => setIsAddHolidayOpen(false)} className="px-3 py-1.5 rounded-lg text-slate-600">
                  Cancel
                </button>
                <button
                  disabled={!newName || !newDate || !activeTerm}
                  onClick={() => {
                    addHolidayMutation.mutate({
                      term: activeTerm.id,
                      name: newName,
                      date: newDate,
                      is_academic_holiday: true,
                    });
                  }}
                  className="px-4 py-1.5 rounded-lg bg-primary-600 text-white font-semibold disabled:opacity-50"
                >
                  Save Holiday
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
