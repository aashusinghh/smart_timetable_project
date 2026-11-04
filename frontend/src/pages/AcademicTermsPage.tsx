import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  Calendar,
  Clock,
  Plus,
  Trash2,
  X,
  CheckCircle,
  Coffee,
  Sun,
  Sunset,
} from 'lucide-react';
import { academicsService } from '../services/academics';
import { AcademicYear, AcademicTerm } from '../types';

const yearSchema = z.object({
  name: z.string().min(4, 'e.g. 2026-27'),
  start_date: z.string().min(10, 'Start date required'),
  end_date: z.string().min(10, 'End date required'),
  is_current: z.boolean().default(false),
});

const termSchema = z.object({
  academic_year: z.coerce.number().min(1, 'Select an academic year'),
  name: z.string().min(3, 'e.g. Odd Semester 2026-27'),
  term_type: z.enum(['ODD', 'EVEN', 'SUMMER']),
  start_date: z.string().min(10, 'Start date required'),
  end_date: z.string().min(10, 'End date required'),
  is_active: z.boolean().default(true),
});

type YearFormData = z.infer<typeof yearSchema>;
type TermFormData = z.infer<typeof termSchema>;

export const AcademicTermsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [isYearModalOpen, setIsYearModalOpen] = useState(false);
  const [isTermModalOpen, setIsTermModalOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Queries
  const { data: years = [], isLoading: loadingYears } = useQuery({
    queryKey: ['academic-years'],
    queryFn: academicsService.getAcademicYears,
  });

  const { data: terms = [], isLoading: loadingTerms } = useQuery({
    queryKey: ['academic-terms'],
    queryFn: () => academicsService.getAcademicTerms(),
  });

  const { data: timeSlots = [] } = useQuery({
    queryKey: ['time-slots'],
    queryFn: academicsService.getTimeSlots,
  });

  // Forms
  const {
    register: regYear,
    handleSubmit: handleYearSubmit,
    reset: resetYear,
    formState: { errors: yearErrors, isSubmitting: isSubmittingYear },
  } = useForm<YearFormData>({
    resolver: zodResolver(yearSchema),
    defaultValues: {
      name: '',
      start_date: '',
      end_date: '',
      is_current: false,
    },
  });

  const {
    register: regTerm,
    handleSubmit: handleTermSubmit,
    reset: resetTerm,
    formState: { errors: termErrors, isSubmitting: isSubmittingTerm },
  } = useForm<TermFormData>({
    resolver: zodResolver(termSchema),
    defaultValues: {
      academic_year: years[0]?.id || 0,
      name: '',
      term_type: 'ODD',
      start_date: '',
      end_date: '',
      is_active: true,
    },
  });

  // Mutations
  const createYearMutation = useMutation({
    mutationFn: (data: Partial<AcademicYear>) => academicsService.createAcademicYear(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academic-years'] });
      setIsYearModalOpen(false);
      resetYear();
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.name?.[0] || 'Failed to create academic year.');
    },
  });

  const deleteYearMutation = useMutation({
    mutationFn: (id: number) => academicsService.deleteAcademicYear(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['academic-years'] }),
  });

  const createTermMutation = useMutation({
    mutationFn: (data: Partial<AcademicTerm>) => academicsService.createAcademicTerm(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academic-terms'] });
      setIsTermModalOpen(false);
      resetTerm();
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.detail || 'Failed to create academic term.');
    },
  });

  const deleteTermMutation = useMutation({
    mutationFn: (id: number) => academicsService.deleteAcademicTerm(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['academic-terms'] }),
  });

  const morningSlots = timeSlots.filter((s) => s.session === 'MORNING' || s.slot_no <= 4);
  const afternoonSlots = timeSlots.filter((s) => s.session === 'AFTERNOON' || s.slot_no > 4);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary-50 dark:bg-primary-950/70 text-primary-700 dark:text-primary-300 mb-2">
            <Calendar className="w-3.5 h-3.5" />
            <span>Academic Calendar & Slots</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Academic Calendar & Time Slots</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Configure academic years, semester terms, and inspect university daily scheduling slots.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setErrorMessage(null);
              setIsYearModalOpen(true);
            }}
            className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-100 transition-colors"
          >
            + Add Academic Year
          </button>
          <button
            onClick={() => {
              setErrorMessage(null);
              setIsTermModalOpen(true);
            }}
            className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-primary-600 hover:bg-primary-700 text-white shadow-sm transition-colors"
          >
            + Add Academic Term
          </button>
        </div>
      </div>

      {/* Grid: Academic Years & Terms */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Academic Years Card */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">Academic Years</h2>
            <span className="text-xs text-slate-400">{years.length} configured</span>
          </div>
          <div className="space-y-2.5">
            {years.map((y) => (
              <div
                key={y.id}
                className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 text-xs"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 dark:text-white text-sm">{y.name}</span>
                    {y.is_current && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                        Current
                      </span>
                    )}
                  </div>
                  <span className="text-slate-500 text-[11px] block mt-0.5">
                    {y.start_date} → {y.end_date}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 text-[11px]">{y.terms_count || 0} terms</span>
                  <button
                    onClick={() => {
                      if (confirm(`Delete year ${y.name}?`)) deleteYearMutation.mutate(y.id);
                    }}
                    className="p-1 text-slate-400 hover:text-rose-600 rounded transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Academic Terms Card */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">Academic Terms</h2>
            <span className="text-xs text-slate-400">{terms.length} active terms</span>
          </div>
          <div className="space-y-2.5">
            {terms.map((t) => (
              <div
                key={t.id}
                className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 text-xs"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 dark:text-white">{t.name}</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-primary-100 text-primary-800 dark:bg-primary-950 dark:text-primary-300">
                      {t.term_type}
                    </span>
                  </div>
                  <span className="text-slate-500 text-[11px] block mt-0.5">
                    Year: {t.year_name || 'Academic Year'} • {t.start_date} → {t.end_date}
                  </span>
                </div>
                <button
                  onClick={() => {
                    if (confirm(`Delete term ${t.name}?`)) deleteTermMutation.mutate(t.id);
                  }}
                  className="p-1 text-slate-400 hover:text-rose-600 rounded transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* University Time Slots Visualizer (§6 of architecture spec) */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-5">
        <div>
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
            <Clock className="w-4 h-4 text-primary-500" />
            <span>Architecture Specification §6</span>
          </div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">
            Daily Standard Time Slots (8 One-Hour Slots)
          </h2>
          <p className="text-xs text-slate-500 max-w-2xl">
            Each day has 8 standard one-hour slots with an enforced lunch break from 12:30 to 14:00.
            Continuous 3-hour labs are permitted only within (08:30–11:30, 09:30–12:30, 14:00–17:00, 15:00–18:00).
          </p>
        </div>

        {/* Morning Session */}
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider mb-2">
            <Sun className="w-4 h-4" />
            <span>Morning Session (08:30 – 12:30)</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {morningSlots.map((slot) => (
              <div
                key={slot.id || slot.slot_no}
                className="p-3.5 rounded-xl border border-amber-200/60 dark:border-amber-900/40 bg-amber-50/40 dark:bg-amber-950/20 text-xs"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-slate-900 dark:text-white">Slot {slot.slot_no}</span>
                  <span className="text-[10px] font-semibold text-amber-700 dark:text-amber-300">1 Hour</span>
                </div>
                <div className="text-sm font-extrabold text-amber-800 dark:text-amber-300">
                  {slot.start_time.slice(0, 5)} - {slot.end_time.slice(0, 5)}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Lunch Break Visual Gap */}
        <div className="flex items-center justify-center gap-2 py-3 rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-dashed border-slate-300 dark:border-slate-700 text-xs font-semibold text-slate-600 dark:text-slate-400">
          <Coffee className="w-4 h-4 text-amber-600" />
          <span>Lunch Break (12:30 – 14:00) — No classes can cross or be scheduled</span>
        </div>

        {/* Afternoon Session */}
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider mb-2">
            <Sunset className="w-4 h-4" />
            <span>Afternoon Session (14:00 – 18:00)</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {afternoonSlots.map((slot) => (
              <div
                key={slot.id || slot.slot_no}
                className="p-3.5 rounded-xl border border-indigo-200/60 dark:border-indigo-900/40 bg-indigo-50/40 dark:bg-indigo-950/20 text-xs"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-slate-900 dark:text-white">Slot {slot.slot_no}</span>
                  <span className="text-[10px] font-semibold text-indigo-700 dark:text-indigo-300">1 Hour</span>
                </div>
                <div className="text-sm font-extrabold text-indigo-800 dark:text-indigo-300">
                  {slot.start_time.slice(0, 5)} - {slot.end_time.slice(0, 5)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Add Year Modal */}
      {isYearModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-sm w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-900 dark:text-white">Add Academic Year</h2>
              <button onClick={() => setIsYearModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>
            {errorMessage && <div className="text-xs text-rose-500">{errorMessage}</div>}
            <form onSubmit={handleYearSubmit((d) => createYearMutation.mutate(d))} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold block mb-1">Year Name</label>
                <input type="text" placeholder="e.g. 2026-27" {...regYear('name')} className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800" />
                {yearErrors.name && <p className="text-rose-500 mt-1">{yearErrors.name.message}</p>}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="font-semibold block mb-1">Start Date</label>
                  <input type="date" {...regYear('start_date')} className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800" />
                </div>
                <div>
                  <label className="font-semibold block mb-1">End Date</label>
                  <input type="date" {...regYear('end_date')} className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800" />
                </div>
              </div>
              <label className="flex items-center gap-2 cursor-pointer pt-1">
                <input type="checkbox" {...regYear('is_current')} className="rounded" />
                <span>Mark as Current Academic Year</span>
              </label>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button type="button" onClick={() => setIsYearModalOpen(false)} className="px-3 py-1.5 rounded-lg text-slate-600">Cancel</button>
                <button type="submit" disabled={isSubmittingYear} className="px-4 py-1.5 rounded-lg bg-primary-600 text-white font-semibold">Save Year</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Term Modal */}
      {isTermModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-sm w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-900 dark:text-white">Add Academic Term</h2>
              <button onClick={() => setIsTermModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>
            {errorMessage && <div className="text-xs text-rose-500">{errorMessage}</div>}
            <form onSubmit={handleTermSubmit((d) => createTermMutation.mutate(d))} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold block mb-1">Academic Year</label>
                <select {...regTerm('academic_year')} className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800">
                  {years.map((y) => (
                    <option key={y.id} value={y.id}>{y.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="font-semibold block mb-1">Term Name</label>
                <input type="text" placeholder="e.g. Odd Semester 2026-27" {...regTerm('name')} className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800" />
                {termErrors.name && <p className="text-rose-500 mt-1">{termErrors.name.message}</p>}
              </div>
              <div>
                <label className="font-semibold block mb-1">Term Type</label>
                <select {...regTerm('term_type')} className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800">
                  <option value="ODD">Odd Semester</option>
                  <option value="EVEN">Even Semester</option>
                  <option value="SUMMER">Summer Term</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="font-semibold block mb-1">Start Date</label>
                  <input type="date" {...regTerm('start_date')} className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800" />
                </div>
                <div>
                  <label className="font-semibold block mb-1">End Date</label>
                  <input type="date" {...regTerm('end_date')} className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800" />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button type="button" onClick={() => setIsTermModalOpen(false)} className="px-3 py-1.5 rounded-lg text-slate-600">Cancel</button>
                <button type="submit" disabled={isSubmittingTerm} className="px-4 py-1.5 rounded-lg bg-primary-600 text-white font-semibold">Save Term</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
