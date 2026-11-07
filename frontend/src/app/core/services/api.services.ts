/**
 * Servicios de comunicación con el backend, uno por dominio.
 * Ningún componente usa HttpClient directamente.
 */
import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  ActivityAdminDetail, ActivityDetail, ActivitySummary, ActivityWrite, AnswerFeedback, AttemptHistoryItem,
  AttemptResult, AttemptStart, Badge, Category, Challenge, Classroom, ClassroomStats, CompanionStatus, Level,
  Message, OverviewStats, Page, ProgressSummary, ReadingCompletion, ReadingDetail, ReadingHistoryItem,
  ReadingSummary, ReadingWrite, Reward, Role, Student, StudentBadge, StudentChallenge, StudentDashboard, User,
} from '../models/api.models';

const API = environment.apiUrl;

function params(obj: Record<string, unknown>): HttpParams {
  let p = new HttpParams();
  for (const [k, v] of Object.entries(obj)) {
    if (v !== null && v !== undefined && v !== '') p = p.set(k, String(v));
  }
  return p;
}

export interface ReadingFilters {
  category_id?: number | null; difficulty?: number | null; age?: number | null; length?: string | null;
  comprehension?: string | null; q?: string | null; include_unpublished?: boolean; page?: number; size?: number;
}

@Injectable({ providedIn: 'root' })
export class ContentService {
  private readonly http = inject(HttpClient);

  categories(): Observable<Category[]> { return this.http.get<Category[]>(`${API}/categories`); }
  createCategory(data: Partial<Category>): Observable<Category> { return this.http.post<Category>(`${API}/categories`, data); }
  updateCategory(id: number, data: Partial<Category>): Observable<Category> { return this.http.patch<Category>(`${API}/categories/${id}`, data); }
  deleteCategory(id: number): Observable<void> { return this.http.delete<void>(`${API}/categories/${id}`); }

  readings(filters: ReadingFilters = {}): Observable<Page<ReadingSummary>> {
    return this.http.get<Page<ReadingSummary>>(`${API}/readings`, { params: params({ ...filters }) });
  }
  reading(id: number): Observable<ReadingDetail> { return this.http.get<ReadingDetail>(`${API}/readings/${id}`); }
  createReading(data: ReadingWrite): Observable<ReadingDetail> { return this.http.post<ReadingDetail>(`${API}/readings`, data); }
  updateReading(id: number, data: ReadingWrite): Observable<ReadingDetail> { return this.http.put<ReadingDetail>(`${API}/readings/${id}`, data); }
  deleteReading(id: number): Observable<void> { return this.http.delete<void>(`${API}/readings/${id}`); }

  activities(filters: Record<string, unknown> = {}): Observable<Page<ActivitySummary>> {
    return this.http.get<Page<ActivitySummary>>(`${API}/activities`, { params: params(filters) });
  }
  activity(id: number): Observable<ActivityDetail> { return this.http.get<ActivityDetail>(`${API}/activities/${id}`); }
  activityAdmin(id: number): Observable<ActivityAdminDetail> { return this.http.get<ActivityAdminDetail>(`${API}/activities/${id}/admin`); }
  createActivity(data: ActivityWrite): Observable<ActivityAdminDetail> { return this.http.post<ActivityAdminDetail>(`${API}/activities`, data); }
  updateActivity(id: number, data: ActivityWrite): Observable<ActivityAdminDetail> { return this.http.put<ActivityAdminDetail>(`${API}/activities/${id}`, data); }
  deleteActivity(id: number): Observable<void> { return this.http.delete<void>(`${API}/activities/${id}`); }
}

/** Acciones del estudiante autenticado. */
@Injectable({ providedIn: 'root' })
export class LearningService {
  private readonly http = inject(HttpClient);

  dashboard(): Observable<StudentDashboard> { return this.http.get<StudentDashboard>(`${API}/me/dashboard`); }
  profile(): Observable<Student> { return this.http.get<Student>(`${API}/me/profile`); }
  progress(): Observable<ProgressSummary> { return this.http.get<ProgressSummary>(`${API}/me/progress`); }
  badges(): Observable<StudentBadge[]> { return this.http.get<StudentBadge[]>(`${API}/me/badges`); }
  challenges(): Observable<StudentChallenge[]> { return this.http.get<StudentChallenge[]>(`${API}/me/challenges`); }
  rewards(): Observable<Reward[]> { return this.http.get<Reward[]>(`${API}/me/rewards`); }
  readingHistory(): Observable<ReadingHistoryItem[]> { return this.http.get<ReadingHistoryItem[]>(`${API}/me/readings`); }
  setAvatar(avatar: string): Observable<Student> { return this.http.patch<Student>(`${API}/me/avatar`, { avatar }); }

  startReading(readingId: number): Observable<{ id: number }> { return this.http.post<{ id: number }>(`${API}/readings/${readingId}/sessions`, {}); }
  completeReading(sessionId: number): Observable<ReadingCompletion> {
    return this.http.post<ReadingCompletion>(`${API}/readings/sessions/${sessionId}/complete`, {});
  }
  startAttempt(activityId: number): Observable<AttemptStart> { return this.http.post<AttemptStart>(`${API}/activities/${activityId}/attempts`, {}); }
  answer(attemptId: number, body: { question_id: number; selected_option_id?: number; ordered_option_ids?: number[] }): Observable<AnswerFeedback> {
    return this.http.post<AnswerFeedback>(`${API}/attempts/${attemptId}/answers`, body);
  }
  finish(attemptId: number): Observable<AttemptResult> { return this.http.post<AttemptResult>(`${API}/attempts/${attemptId}/finish`, {}); }
}

/** Docentes y acudientes: aulas, estudiantes y reportes. */
@Injectable({ providedIn: 'root' })
export class SchoolService {
  private readonly http = inject(HttpClient);

  classrooms(): Observable<Classroom[]> { return this.http.get<Classroom[]>(`${API}/classrooms`); }
  createClassroom(data: Partial<Classroom>): Observable<Classroom> { return this.http.post<Classroom>(`${API}/classrooms`, data); }
  updateClassroom(id: number, data: Partial<Classroom>): Observable<Classroom> { return this.http.patch<Classroom>(`${API}/classrooms/${id}`, data); }
  deleteClassroom(id: number): Observable<void> { return this.http.delete<void>(`${API}/classrooms/${id}`); }
  classroomStats(id: number): Observable<ClassroomStats> { return this.http.get<ClassroomStats>(`${API}/classrooms/${id}/stats`); }

  students(): Observable<Student[]> { return this.http.get<Student[]>(`${API}/students`); }
  student(id: number): Observable<Student> { return this.http.get<Student>(`${API}/students/${id}`); }
  createStudent(data: Record<string, unknown>): Observable<Student> { return this.http.post<Student>(`${API}/students`, data); }
  updateStudent(id: number, data: Record<string, unknown>): Observable<Student> { return this.http.patch<Student>(`${API}/students/${id}`, data); }
  resetStudentPassword(id: number, new_password: string): Observable<Message> {
    return this.http.post<Message>(`${API}/students/${id}/reset-password`, { new_password });
  }
  linkCode(id: number): Observable<{ code: string; expires_at: string }> {
    return this.http.post<{ code: string; expires_at: string }>(`${API}/students/${id}/link-code`, {});
  }
  linkStudent(code: string, relationship_label: string | null): Observable<Student> {
    return this.http.post<Student>(`${API}/students/link`, { code, relationship_label });
  }
  progress(id: number): Observable<ProgressSummary> { return this.http.get<ProgressSummary>(`${API}/students/${id}/progress`); }
  attempts(id: number): Observable<AttemptHistoryItem[]> { return this.http.get<AttemptHistoryItem[]>(`${API}/students/${id}/attempts`); }
  readings(id: number): Observable<ReadingHistoryItem[]> { return this.http.get<ReadingHistoryItem[]>(`${API}/students/${id}/readings`); }
  badges(id: number): Observable<StudentBadge[]> { return this.http.get<StudentBadge[]>(`${API}/students/${id}/badges`); }
}

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly http = inject(HttpClient);

  users(filters: { role?: Role | ''; q?: string; is_active?: boolean | ''; page?: number; size?: number }): Observable<Page<User>> {
    return this.http.get<Page<User>>(`${API}/users`, { params: params(filters) });
  }
  createUser(data: Record<string, unknown>): Observable<User> { return this.http.post<User>(`${API}/users`, data); }
  updateUser(id: number, data: Record<string, unknown>): Observable<User> { return this.http.patch<User>(`${API}/users/${id}`, data); }
  resetPassword(id: number, new_password: string): Observable<Message> {
    return this.http.post<Message>(`${API}/users/${id}/reset-password`, { new_password });
  }
  overview(): Observable<OverviewStats> { return this.http.get<OverviewStats>(`${API}/stats/overview`); }
  badges(): Observable<Badge[]> { return this.http.get<Badge[]>(`${API}/badges`); }
  updateBadge(id: number, data: Omit<Badge, 'id'>): Observable<Badge> { return this.http.put<Badge>(`${API}/badges/${id}`, data); }
  challenges(): Observable<Challenge[]> { return this.http.get<Challenge[]>(`${API}/challenges`); }
  createChallenge(data: Omit<Challenge, 'id'>): Observable<Challenge> { return this.http.post<Challenge>(`${API}/challenges`, data); }
  updateChallenge(id: number, data: Omit<Challenge, 'id'>): Observable<Challenge> { return this.http.put<Challenge>(`${API}/challenges/${id}`, data); }
  levels(): Observable<Level[]> { return this.http.get<Level[]>(`${API}/levels`); }
  companionStatus(): Observable<CompanionStatus> { return this.http.get<CompanionStatus>(`${API}/ai-companion/status`); }
}
