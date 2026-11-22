import React from 'react';
import {
  Award,
  Users,
  UserCheck,
  Scale,
  Clock,
  Calendar,
  CalendarCog,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';
import { ConstraintScoreBreakdown, ScheduleMetrics, UnscheduledOffering } from '../../types';

interface ScoringDashboardProps {
  overallScore: number;
  breakdown?: ConstraintScoreBreakdown;
  metrics?: ScheduleMetrics;
  unscheduledOfferings?: UnscheduledOffering[];
  compact?: boolean;
}

export const ScoringDashboard: React.FC<ScoringDashboardProps> = ({
  overallScore,
  breakdown,
  metrics,
  unscheduledOfferings = [],
  compact = false,
}) => {
  const getScoreBadge = (score: number) => {
    if (score >= 90) return { label: 'Optimal', color: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200' };
    if (score >= 75) return { label: 'Good', color: 'text-blue-600 bg-blue-50 dark:bg-blue-950/40 border-blue-200' };
    if (score >= 60) return { label: 'Acceptable', color: 'text-amber-600 bg-amber-50 dark:bg-amber-950/40 border-amber-200' };
    return { label: 'Needs Improvement', color: 'text-red-600 bg-red-50 dark:bg-red-950/40 border-red-200' };
  };

  const badge = getScoreBadge(overallScore);

  const constraintItems = [
    {
      title: 'Student Timetable Gaps',
      description: 'Minimizes idle holes between cohort classes',
      score: breakdown?.student_gaps_score ?? 100,
      icon: Users,
      metricText: metrics ? `${metrics.student_gap_hours} gap hour(s)` : undefined,
    },
    {
      title: 'Professor Timetable Gaps',
      description: 'Compact teaching schedules for faculty',
      score: breakdown?.professor_gaps_score ?? 100,
      icon: UserCheck,
      metricText: metrics ? `${metrics.professor_gap_hours} gap hour(s)` : undefined,
    },
    {
      title: 'Weekday Load Balance',
      description: 'Even distribution of contact hours Monday–Friday',
      score: breakdown?.load_balance_score ?? 100,
      icon: Scale,
    },
    {
      title: 'Consecutive Hours Limit',
      description: 'Prevents faculty fatigue (> 3 hours straight)',
      score: breakdown?.consecutive_hours_score ?? 100,
      icon: Clock,
      metricText: metrics ? `Max streak: ${metrics.max_consecutive_hours} hr(s)` : undefined,
    },
    {
      title: 'Slot Preferences & Distribution',
      description: 'Prioritizes prime mid-day slots (slots 2..7)',
      score: breakdown?.slot_preference_score ?? 100,
      icon: CalendarCog,
    },
    {
      title: 'Multi-Meeting Day Spread',
      description: 'Spreads theory and lab sessions across the week',
      score: breakdown?.day_spread_score ?? 100,
      icon: Calendar,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Score Banner */}
      <div className="bg-white dark:bg-slate-900 rounded-lg p-6 text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-800">

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-lg border border-slate-200 dark:border-slate-700 flex items-center justify-center text-amber-600">
              <Award className="w-8 h-8" strokeWidth={1.5} />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <span className="text-3xl font-semibold tracking-tight">{overallScore.toFixed(1)}</span>
                <span className="text-slate-400 font-semibold text-lg">/ 100</span>
                <span className={`text-xs px-2.5 py-0.5 rounded border font-semibold ${badge.color}`}>
                  {badge.label}
                </span>
              </div>
              <h4 className="text-sm font-medium text-slate-500 dark:text-slate-400 mt-1">
                Schedule Quality Evaluation
              </h4>
            </div>
          </div>

          {metrics && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-md p-3 text-center">
              <div>
                <p className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Scheduled</p>
                <p className="text-lg font-semibold text-emerald-700 dark:text-emerald-400">{metrics.total_scheduled_meetings}</p>
              </div>
              <div>
                <p className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Unscheduled</p>
                <p className={`text-lg font-semibold ${metrics.total_unscheduled_meetings > 0 ? 'text-red-600 dark:text-red-400': 'text-slate-700 dark:text-slate-200'}`}>
                  {metrics.total_unscheduled_meetings}
                </p>
              </div>
              <div>
                <p className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Student Gaps</p>
                <p className="text-lg font-semibold text-amber-700 dark:text-amber-300">{metrics.student_gap_hours}h</p>
              </div>
              <div>
                <p className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Prof Gaps</p>
                <p className="text-lg font-semibold text-blue-700 dark:text-blue-300">{metrics.professor_gap_hours}h</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Soft Constraint Score Breakdown */}
      <div>
        <h4 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3 flex items-center gap-2">
          <Scale className="w-4 h-4 text-primary-500" />
          Soft Constraint Breakdown
        </h4>

        <div className={`grid ${compact ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2'} gap-3.5`}>
          {constraintItems.map((item, idx) => {
            const Icon = item.icon;
            const progressColor =
              item.score >= 85
                ? 'bg-emerald-500'
                : item.score >= 70
                ? 'bg-blue-500'
                : item.score >= 50
                ? 'bg-amber-500'
                : 'bg-red-500';

            return (
              <div
                key={idx}
                className="p-4 rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 "
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-primary-600 dark:text-primary-400">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h5 className="text-sm font-semibold text-slate-800 dark:text-slate-200">{item.title}</h5>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{item.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-base font-semibold text-slate-900 dark:text-slate-100">
                      {item.score.toFixed(0)}%
                    </span>
                    {item.metricText && (
                      <span className="block text-[11px] text-slate-400">{item.metricText}</span>
                    )}
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-[width] duration-500 ${progressColor}`}
                    style={{ width: `${Math.max(4, Math.min(100, item.score))}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Unscheduled Offerings Diagnosis */}
      {unscheduledOfferings.length > 0 && (
        <div className="border border-red-200 dark:border-red-900/60 rounded-lg p-5 bg-red-50/40 dark:bg-red-950/20">
          <div className="flex items-center gap-2.5 text-red-700 dark:text-red-400 mb-3 font-semibold text-sm">
            <AlertTriangle className="w-4 h-4" />
            Unscheduled Offerings ({unscheduledOfferings.length})
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-red-100/60 dark:bg-red-900/30 text-red-900 dark:text-red-200 uppercase font-semibold">
                <tr>
                  <th className="p-2.5 rounded-l-lg">Course</th>
                  <th className="p-2.5">Cohort</th>
                  <th className="p-2.5">Professor</th>
                  <th className="p-2.5 rounded-r-lg">Diagnosis / Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-200/50 dark:divide-red-900/30 text-slate-700 dark:text-slate-300">
                {unscheduledOfferings.map((u, i) => (
                  <tr key={i}>
                    <td className="p-2.5 font-semibold">{u.course_code || '—'} {u.course_name ? `(${u.course_name})` : ''}</td>
                    <td className="p-2.5">{u.cohort || '—'}</td>
                    <td className="p-2.5">{u.professor || '—'}</td>
                    <td className="p-2.5 text-red-600 dark:text-red-400 font-medium">{u.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

