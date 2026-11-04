import React, { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileSpreadsheet,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  Download,
  FileCheck,
  FileX,
  RefreshCw,
} from 'lucide-react';
import { importsService } from '../services/imports';
import { CSVImportResult } from '../types';

export const ImportPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'curriculum' | 'professors'>('curriculum');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [result, setResult] = useState<CSVImportResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const importMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile) throw new Error('No file selected');
      if (activeTab === 'curriculum') {
        return importsService.importCurriculum(selectedFile);
      } else {
        return importsService.importProfessors(selectedFile);
      }
    },
    onSuccess: (data) => {
      setResult(data);
      if (activeTab === 'curriculum') {
        queryClient.invalidateQueries({ queryKey: ['curriculum'] });
        queryClient.invalidateQueries({ queryKey: ['courses'] });
      } else {
        queryClient.invalidateQueries({ queryKey: ['professors'] });
      }
    },
    onError: (err: any) => {
      if (err.response?.data) {
        setResult(err.response.data);
      } else {
        setResult({
          success: false,
          imported_count: 0,
          errors: [{ row: 0, message: err.message || 'Import failed.' }],
        });
      }
    },
  });

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.csv')) {
        setSelectedFile(file);
        setResult(null);
      } else {
        alert('Please drop a valid .csv file.');
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setResult(null);
    }
  };

  const downloadCurriculumTemplate = () => {
    const csvContent =
      'branch_code,semester_no,course_code,course_name,credit,course_type,weekly_meetings,duration_slots\n' +
      'BTECH_CSE,3,CS301,Database Management Systems,3,THEORY,3,1\n' +
      'BTECH_CSE,3,CS302,Operating Systems Lab,2,LAB,2,3\n' +
      'MCA,1,CA101,Object Oriented Programming,4,THEORY,4,1\n';
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'curriculum_import_template.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const downloadProfessorsTemplate = () => {
    const csvContent =
      'email,full_name,employee_code,department_code,designation,max_hours_per_day\n' +
      'dr.grace.hopper@university.edu,Dr. Grace Hopper,EMP010,CSE,Professor,6\n' +
      'dr.alan.kay@university.edu,Dr. Alan Kay,EMP011,CSE,Associate Professor,5\n' +
      'dr.barbara.liskov@university.edu,Dr. Barbara Liskov,EMP012,CSE,Professor,6\n';
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'professors_import_template.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary-50 dark:bg-primary-950/70 text-primary-700 dark:text-primary-300 mb-2">
          <FileSpreadsheet className="w-3.5 h-3.5" />
          <span>Bulk Data Ingestion</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">CSV Data Import</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Upload CSV files to batch-import curriculum structures or faculty members with row-level error validation.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-3 border-b border-slate-200 dark:border-slate-800 pb-3">
        <button
          onClick={() => {
            setActiveTab('curriculum');
            setSelectedFile(null);
            setResult(null);
          }}
          className={`px-4 py-2 text-xs font-bold rounded-lg transition-colors ${
            activeTab === 'curriculum'
              ? 'bg-primary-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
          }`}
        >
          Curriculum & Courses Import
        </button>
        <button
          onClick={() => {
            setActiveTab('professors');
            setSelectedFile(null);
            setResult(null);
          }}
          className={`px-4 py-2 text-xs font-bold rounded-lg transition-colors ${
            activeTab === 'professors'
              ? 'bg-primary-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
          }`}
        >
          Professors & Faculty Import
        </button>
      </div>

      {/* Upload & Action Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left 2 Cols: Drag & Drop Zone */}
        <div className="md:col-span-2 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
              dragOver
                ? 'border-primary-500 bg-primary-50/50 dark:bg-primary-950/20'
                : 'border-slate-300 dark:border-slate-700 hover:border-primary-400'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept=".csv"
              className="hidden"
            />
            <UploadCloud className="w-10 h-10 text-primary-500 mx-auto mb-3" />
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
              {selectedFile ? selectedFile.name : 'Choose a CSV file or drag and drop it here'}
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Supports .csv files up to 10MB formatted according to specification.
            </p>
            {selectedFile && (
              <span className="inline-block mt-3 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                Ready to Import: {(selectedFile.size / 1024).toFixed(1)} KB
              </span>
            )}
          </div>

          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-slate-400">
              Imports are processed in an atomic database transaction.
            </span>
            <button
              onClick={() => importMutation.mutate()}
              disabled={!selectedFile || importMutation.isPending}
              className="px-5 py-2.5 rounded-lg bg-primary-600 text-white font-semibold text-xs shadow-sm hover:bg-primary-700 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              {importMutation.isPending ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Processing CSV...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Upload & Run Import</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Col: Template Instructions & Download */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4 text-xs">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-primary-500" />
            <span>CSV File Template</span>
          </h2>

          <p className="text-slate-500">
            {activeTab === 'curriculum'
              ? 'Download the standard curriculum CSV template containing branch code, semester, credit, and meeting delivery rules.'
              : 'Download the faculty CSV template with email, full name, employee code, department, and daily load.'}
          </p>

          <button
            onClick={
              activeTab === 'curriculum'
                ? downloadCurriculumTemplate
                : downloadProfessorsTemplate
            }
            className="w-full py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 font-semibold text-slate-800 dark:text-slate-200 transition-colors flex items-center justify-center gap-2"
          >
            <Download className="w-4 h-4" />
            <span>Download Sample CSV Template</span>
          </button>

          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 space-y-2">
            <span className="font-semibold text-slate-700 dark:text-slate-300 block">Required Columns:</span>
            {activeTab === 'curriculum' ? (
              <ul className="list-disc pl-4 space-y-1 text-slate-500 font-mono text-[11px]">
                <li>branch_code (e.g. BTECH_CSE)</li>
                <li>semester_no (1..8)</li>
                <li>course_code (e.g. CS301)</li>
                <li>course_name</li>
                <li>credit (1..6)</li>
                <li>course_type (THEORY, LAB)</li>
                <li>weekly_meetings (optional)</li>
                <li>duration_slots (optional)</li>
              </ul>
            ) : (
              <ul className="list-disc pl-4 space-y-1 text-slate-500 font-mono text-[11px]">
                <li>email (university email)</li>
                <li>full_name</li>
                <li>department_code (e.g. CSE)</li>
                <li>employee_code (optional)</li>
                <li>designation (optional)</li>
                <li>max_hours_per_day (1..12)</li>
              </ul>
            )}
          </div>
        </div>
      </div>

      {/* Import Result Feedback */}
      {result && (
        <div
          className={`p-6 rounded-2xl border shadow-sm space-y-4 ${
            result.success
              ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800/60'
              : 'bg-rose-50 dark:bg-rose-950/20 border-rose-200 dark:border-rose-800/60'
          }`}
        >
          <div className="flex items-center gap-3">
            {result.success ? (
              <CheckCircle2 className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
            ) : (
              <FileX className="w-6 h-6 text-rose-600 dark:text-rose-400" />
            )}
            <div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                {result.success ? 'Import Completed Successfully!' : 'Import Failed — Errors Detected'}
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-300">
                {result.success
                  ? `Successfully imported and persisted ${result.imported_count} record(s).`
                  : 'No changes were saved to the database. Fix the errors below and try again.'}
              </p>
            </div>
          </div>

          {result.errors && result.errors.length > 0 && (
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-rose-200 dark:border-rose-900/60 overflow-hidden text-xs">
              <div className="p-3 bg-rose-100/60 dark:bg-rose-950/40 font-bold text-rose-900 dark:text-rose-200 border-b border-rose-200 dark:border-rose-900/40">
                Row-Level Error Report ({result.errors.length} issues)
              </div>
              <div className="divide-y divide-slate-100 dark:divide-slate-800 max-h-60 overflow-y-auto">
                {result.errors.map((err, i) => (
                  <div key={i} className="p-3 flex items-start gap-3">
                    <span className="px-2 py-0.5 rounded font-mono font-bold bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 text-[10px]">
                      Row {err.row}
                    </span>
                    <span className="text-slate-700 dark:text-slate-300">{err.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
