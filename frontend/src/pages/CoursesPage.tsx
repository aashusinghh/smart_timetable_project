import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  BookOpen,
  Plus,
  Edit2,
  Trash2,
  X,
  Search,
  Layers,
  Clock,
  Sparkles,
  FlaskConical,
} from 'lucide-react';
import { academicsService } from '../services/academics';
import { Course, CourseType, Department } from '../types';

const courseSchema = z.object({
  code: z.string().min(2, 'Code must be at least 2 chars').max(30),
  name: z.string().min(3, 'Course title required').max(150),
  credit: z.coerce.number().min(1).max(10),
  course_type: z.enum(['THEORY', 'LAB', 'PROJECT', 'SEMINAR']),
  department: z.coerce.number().optional().nullable(),
  description: z.string().optional(),
  weekly_meetings: z.coerce.number().min(1).max(10),
  duration_slots: z.coerce.number().min(1).max(4),
  preferred_room_type: z.string().default('CLASSROOM'),
});

type CourseFormData = z.infer<typeof courseSchema>;

export const CoursesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [deptFilter, setDeptFilter] = useState<number | undefined>();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCourse, setEditingCourse] = useState<Course | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Queries
  const { data: departments = [] } = useQuery({
    queryKey: ['departments'],
    queryFn: academicsService.getDepartments,
  });

  const { data: courses = [], isLoading } = useQuery({
    queryKey: ['courses', typeFilter, deptFilter],
    queryFn: () =>
      academicsService.getCourses({
        course_type: typeFilter || undefined,
        department: deptFilter,
      }),
  });

  // Form
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<CourseFormData>({
    resolver: zodResolver(courseSchema),
    defaultValues: {
      code: '',
      name: '',
      credit: 3,
      course_type: 'THEORY',
      weekly_meetings: 3,
      duration_slots: 1,
      preferred_room_type: 'CLASSROOM',
    },
  });

  const selectedType = watch('course_type');
  const weeklyMeetings = watch('weekly_meetings') || 1;
  const durationSlots = watch('duration_slots') || 1;
  const totalHours = weeklyMeetings * durationSlots;

  // Auto-adjust default delivery rules when course type changes
  const onCourseTypeChange = (type: CourseType) => {
    setValue('course_type', type);
    if (type === 'LAB') {
      setValue('credit', 2);
      setValue('weekly_meetings', 2);
      setValue('duration_slots', 3);
      setValue('preferred_room_type', 'COMPUTER_LAB');
    } else if (type === 'THEORY') {
      setValue('credit', 3);
      setValue('weekly_meetings', 3);
      setValue('duration_slots', 1);
      setValue('preferred_room_type', 'CLASSROOM');
    } else if (type === 'SEMINAR') {
      setValue('credit', 1);
      setValue('weekly_meetings', 1);
      setValue('duration_slots', 1);
      setValue('preferred_room_type', 'SEMINAR_HALL');
    }
  };

  // Mutations
  const saveMutation = useMutation({
    mutationFn: async (data: CourseFormData) => {
      const payload: any = {
        code: data.code,
        name: data.name,
        credit: data.credit,
        course_type: data.course_type,
        department: data.department || null,
        description: data.description || '',
        delivery_rule: {
          weekly_meetings: data.weekly_meetings,
          duration_slots: data.duration_slots,
          preferred_room_type: data.preferred_room_type,
        },
      };
      if (editingCourse) {
        return academicsService.updateCourse(editingCourse.id, payload);
      }
      return academicsService.createCourse(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courses'] });
      setIsModalOpen(false);
      reset();
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.code?.[0] || err.response?.data?.detail || 'Failed to save course.');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => academicsService.deleteCourse(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['courses'] }),
  });

  const openCreateModal = () => {
    setEditingCourse(null);
    reset({
      code: '',
      name: '',
      credit: 3,
      course_type: 'THEORY',
      weekly_meetings: 3,
      duration_slots: 1,
      preferred_room_type: 'CLASSROOM',
    });
    setErrorMessage(null);
    setIsModalOpen(true);
  };

  const openEditModal = (c: Course) => {
    setEditingCourse(c);
    setValue('code', c.code);
    setValue('name', c.name);
    setValue('credit', c.credit);
    setValue('course_type', c.course_type);
    setValue('department', c.department || undefined);
    setValue('description', c.description || '');
    setValue('weekly_meetings', c.delivery_rule?.weekly_meetings || 3);
    setValue('duration_slots', c.delivery_rule?.duration_slots || 1);
    setValue('preferred_room_type', c.delivery_rule?.preferred_room_type || 'CLASSROOM');
    setErrorMessage(null);
    setIsModalOpen(true);
  };

  const filteredCourses = courses.filter((c) =>
    c.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary-50 dark:bg-primary-950/70 text-primary-700 dark:text-primary-300 mb-2">
            <BookOpen className="w-3.5 h-3.5" />
            <span>Curriculum & Catalog</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">University Course Catalog</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Define courses, credit values, and enforce weekly meeting delivery rules (e.g. 2×3h labs, 3×1h theory).
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-primary-600 text-white hover:bg-primary-700 shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Course</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search courses by code or title..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
          />
        </div>

        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
        >
          <option value="">All Types</option>
          <option value="THEORY">Theory</option>
          <option value="LAB">Laboratory</option>
          <option value="PROJECT">Project</option>
          <option value="SEMINAR">Seminar</option>
        </select>

        <select
          value={deptFilter || ''}
          onChange={(e) => setDeptFilter(e.target.value ? Number(e.target.value) : undefined)}
          className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
        >
          <option value="">All Departments</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name} ({d.code})
            </option>
          ))}
        </select>
      </div>

      {/* Courses List */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading courses...</div>
        ) : filteredCourses.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">No courses found matching criteria.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="px-5 py-3">Code & Name</th>
                  <th className="px-5 py-3">Type</th>
                  <th className="px-5 py-3">Credits</th>
                  <th className="px-5 py-3">Weekly Schedule Pattern</th>
                  <th className="px-5 py-3">Department</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredCourses.map((c) => {
                  const rule = c.delivery_rule;
                  const isLab = c.course_type === 'LAB';
                  return (
                    <tr key={c.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="px-5 py-3.5 font-bold text-slate-900 dark:text-white">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-primary-600 dark:text-primary-400">{c.code}</span>
                          <span>— {c.name}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          className={`inline-block px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${
                            isLab
                              ? 'bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300'
                              : 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300'
                          }`}
                        >
                          {c.course_type_display || c.course_type}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 font-semibold">{c.credit} Credits</td>
                      <td className="px-5 py-3.5">
                        {rule ? (
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                              {rule.weekly_meetings} × {rule.duration_slots}h
                            </span>
                            <span className="text-[11px] text-slate-400">
                              ({rule.weekly_meetings * rule.duration_slots} contact hrs/wk)
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400">Standard</span>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-slate-500">
                        {c.department_name ? `${c.department_name} (${c.department_code})` : 'University-wide'}
                      </td>
                      <td className="px-5 py-3.5 text-right space-x-2">
                        <button
                          onClick={() => openEditModal(c)}
                          className="p-1.5 text-slate-500 hover:text-primary-600 rounded-lg"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            if (confirm(`Delete course ${c.code}?`)) deleteMutation.mutate(c.id);
                          }}
                          className="p-1.5 text-slate-500 hover:text-rose-600 rounded-lg"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add / Edit Course Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                {editingCourse ? 'Edit Course' : 'Add New Course'}
              </h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            {errorMessage && (
              <div className="p-3 text-xs rounded-lg bg-rose-50 text-rose-700 dark:bg-rose-950/50">
                {errorMessage}
              </div>
            )}

            <form onSubmit={handleSubmit((d) => saveMutation.mutate(d))} className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold block mb-1">Course Code</label>
                  <input
                    type="text"
                    placeholder="e.g. CS301"
                    {...register('code')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-mono"
                  />
                  {errors.code && <p className="text-rose-500 mt-1">{errors.code.message}</p>}
                </div>

                <div>
                  <label className="font-semibold block mb-1">Course Type</label>
                  <select
                    value={selectedType}
                    onChange={(e) => onCourseTypeChange(e.target.value as CourseType)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                  >
                    <option value="THEORY">Theory</option>
                    <option value="LAB">Practical / Lab</option>
                    <option value="PROJECT">Project Work</option>
                    <option value="SEMINAR">Seminar</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="font-semibold block mb-1">Course Title</label>
                <input
                  type="text"
                  placeholder="e.g. Database Management Systems"
                  {...register('name')}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                />
                {errors.name && <p className="text-rose-500 mt-1">{errors.name.message}</p>}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold block mb-1">Academic Credits</label>
                  <input
                    type="number"
                    {...register('credit')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                  />
                </div>
                <div>
                  <label className="font-semibold block mb-1">Department</label>
                  <select
                    {...register('department')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                  >
                    <option value="">University-wide / None</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.code})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Delivery Rule Box (§5.3 Architecture Spec) */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    Weekly Delivery Rule (§5.3 Contact Spec)
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-primary-100 text-primary-800 dark:bg-primary-950 dark:text-primary-300">
                    Total: {totalHours} Contact Hours
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-medium text-slate-500 mb-1">
                      Weekly Meetings (days/wk)
                    </label>
                    <input
                      type="number"
                      {...register('weekly_meetings')}
                      className="w-full px-2.5 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-slate-500 mb-1">
                      Duration (slots per meeting)
                    </label>
                    <input
                      type="number"
                      {...register('duration_slots')}
                      className="w-full px-2.5 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-slate-500 mb-1">
                    Preferred Room Type
                  </label>
                  <select
                    {...register('preferred_room_type')}
                    className="w-full px-2.5 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800"
                  >
                    <option value="CLASSROOM">Classroom</option>
                    <option value="COMPUTER_LAB">Computer Lab</option>
                    <option value="ELECTRONICS_LAB">Electronics Lab</option>
                    <option value="CHEMISTRY_LAB">Chemistry Lab</option>
                    <option value="SEMINAR_HALL">Seminar Hall</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-primary-600 text-white font-semibold shadow-sm hover:bg-primary-700"
                >
                  {isSubmitting ? 'Saving...' : editingCourse ? 'Update Course' : 'Create Course'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
