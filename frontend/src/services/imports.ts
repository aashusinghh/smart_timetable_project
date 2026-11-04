import { api } from './api';
import { CSVImportResult } from '../types';

export const importsService = {
  importCurriculum: async (file: File): Promise<CSVImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post<CSVImportResult>('/curriculum/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  importProfessors: async (file: File): Promise<CSVImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post<CSVImportResult>('/professors/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
};
