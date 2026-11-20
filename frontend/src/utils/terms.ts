import { AcademicTerm } from '../types';

/**
 * The term to show by default: the one running today, otherwise the next one
 * to start, otherwise the first in the list.
 */
export function pickCurrentTerm(terms: AcademicTerm[]): AcademicTerm | undefined {
  if (terms.length === 0) return undefined;
  const today = new Date().toISOString().slice(0, 10);
  const running = terms.find((t) => t.start_date <= today && today <= t.end_date);
  if (running) return running;
  const upcoming = [...terms]
    .filter((t) => t.start_date > today)
    .sort((a, b) => a.start_date.localeCompare(b.start_date))[0];
  return upcoming || terms[0];
}
