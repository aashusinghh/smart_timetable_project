import { AcademicTerm } from '../types';

/**
 * Format academic term names to clean, standardized text:
 * e.g. "Odd Semester 2026-27 (Autumn)" -> "Odd Semester 2026 - 2027"
 * "Even Semester 2026-27 (Spring)" -> "Even Semester 2026 - 2027"
 */
export function formatTermName(name?: string | null): string {
  if (!name) return '';
  return name
    .replace(/\s*\((?:Autumn|Spring|autumn|spring)\)/gi, '')
    .replace(/(\d{4})-(\d{2})(?!\d)/g, (_, y1, y2) => `${y1} - 20${y2}`)
    .trim();
}

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
