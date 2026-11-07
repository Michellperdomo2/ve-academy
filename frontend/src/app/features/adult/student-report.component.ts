import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, OnInit, computed, inject, input, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { AttemptHistoryItem, Classroom, ProgressSummary, ReadingHistoryItem, Student, StudentBadge } from '../../core/models/api.models';
import { ACTIVITY_TYPE_LABELS, SKILL_LABELS, avatarIcon } from '../../core/models/labels';
import { errorMessage } from '../../core/interceptors/interceptors';
import { SchoolService } from '../../core/services/api.services';
import { AuthService } from '../../core/services/auth.service';
import { ConfirmService, ToastService } from '../../core/services/ui.services';
import { SkillBarsComponent } from '../../shared/components/skill-bars.component';
import { WeeklyChartComponent } from '../../shared/components/weekly-chart.component';

/** Reporte de progreso de un estudiante (docente, acudiente o administrador). */
@Component({
  selector: 've-student-report',
  imports: [RouterLink, DatePipe, DecimalPipe, ReactiveFormsModule, SkillBarsComponent, WeeklyChartComponent],
  template: `
    <a [routerLink]="backLink()" class="back">← Volver</a>
    @if (student() && progress()) {
      @let s = student()!;
      @let p = progress()!;
      <header class="head">
        <span class="av">{{ avatar(s.avatar) }}</span>
        <div>
          <h1>{{ s.display_name }}</h1>
          <p class="muted">Usuario: {{ s.username }} · {{ s.classroom_name ?? 'Sin aula' }} @if (s.age) { · {{ s.age }} años }
            @if (s.guardian_names.length) { · Acudientes: {{ s.guardian_names.join(', ') }} }</p>
        </div>
        <button class="btn btn-ghost btn-sm" type="button" (click)="manage.set(!manage())">{{ manage() ? 'Cerrar gestión' : 'Gestionar cuenta' }}</button>
      </header>

      @if (manage()) {
        <section class="panel manage">
          <form class="form" [formGroup]="editForm" (ngSubmit)="save()">
            <h3>Datos del estudiante</h3>
            <div class="form-row">
              <div class="field"><label for="dn">Nombre para mostrar</label><input id="dn" formControlName="display_name" /></div>
              <div class="field"><label for="ag">Edad</label><input id="ag" type="number" min="4" max="12" formControlName="age" /></div>
              @if (canChangeClassroom()) {
                <div class="field"><label for="cl">Aula</label>
                  <select id="cl" formControlName="classroom_id">
                    @for (c of classrooms(); track c.id) { <option [ngValue]="c.id">{{ c.name }}</option> }
                  </select></div>
              }
            </div>
            <div><button class="btn btn-sm" type="submit" [disabled]="editForm.invalid">Guardar cambios</button></div>
          </form>
          <form class="form" [formGroup]="pwForm" (ngSubmit)="resetPassword()">
            <h3>Restablecer contraseña</h3>
            <div class="form-row"><div class="field"><label for="np">Nueva contraseña</label><input id="np" formControlName="new_password" /></div></div>
            <div><button class="btn btn-sm" type="submit" [disabled]="pwForm.invalid">Restablecer</button></div>
          </form>
          <div class="stack">
            @if (canLink()) {
              <h3>Vincular acudiente</h3>
              <p class="muted">Genera un código de un solo uso (7 días) para que el acudiente lo ingrese en su cuenta.</p>
              <div><button class="btn btn-sm" type="button" (click)="linkCode()">Generar código</button></div>
              @if (code(); as c) { <p class="code">{{ c.code }}</p><p class="muted">Vence el {{ c.expires_at | date: 'medium' }}</p> }
            }
            <h3>Estado de la cuenta</h3>
            <div><button class="btn btn-sm" [class.btn-danger]="s.is_active" type="button" (click)="toggleActive(s)">
              {{ s.is_active ? 'Desactivar cuenta' : 'Reactivar cuenta' }}</button></div>
          </div>
        </section>
      }

      <section class="kpis">
        <div class="kpi"><span class="k">{{ p.progress_percent | number: '1.0-0' }}%</span><span class="muted">Avance del catálogo</span></div>
        <div class="kpi"><span class="k">{{ p.readings_completed }}<small>/{{ p.readings_total }}</small></span><span class="muted">Lecturas completadas</span></div>
        <div class="kpi"><span class="k">{{ p.activities_completed }}<small>/{{ p.activities_total }}</small></span><span class="muted">Actividades completadas</span></div>
        <div class="kpi"><span class="k">{{ p.average_score !== null ? (p.average_score | number: '1.0-0') + '%' : '—' }}</span><span class="muted">Puntaje promedio</span></div>
        <div class="kpi"><span class="k">{{ p.correct_answers }}<small> / {{ p.incorrect_answers }}</small></span><span class="muted">Respuestas correctas / incorrectas</span></div>
        <div class="kpi"><span class="k">{{ p.level.icon }} {{ p.level.number }}</span><span class="muted">{{ p.level.name }} · {{ p.total_points }} puntos</span></div>
      </section>

      <div class="grid-2">
        <section class="panel">
          <h2>Habilidades</h2>
          <ve-skill-bars [skills]="p.skills" />
        </section>
        <div class="stack">
          <section class="panel">
            <h2>Últimos 7 días</h2>
            <ve-weekly-chart [days]="p.weekly_activity" />
          </section>
          <section class="panel">
            <h2>Resumen pedagógico</h2>
            <p><strong>Habilidades fortalecidas:</strong> {{ p.strengths.length ? p.strengths.join(', ') : 'aún no hay suficientes datos.' }}</p>
            <p><strong>Necesitan refuerzo:</strong> {{ p.needs_support.length ? p.needs_support.join(', ') : 'ninguna por ahora.' }}</p>
            @if (p.recommendations.length) {
              <p><strong>Actividades sugeridas:</strong></p>
              <ul>@for (r of p.recommendations; track r.activity_id) { <li>{{ r.icon }} {{ r.title }} <span class="muted">({{ r.reason }})</span></li> }</ul>
            }
            <p class="muted small">Estos indicadores describen la práctica dentro de la aplicación; no son un diagnóstico.</p>
          </section>
        </div>
      </div>

      <section class="panel">
        <h2>Historial de actividades</h2>
        <div class="table-wrap">
          <table class="data">
            <thead><tr><th>Fecha</th><th>Actividad</th><th>Tipo</th><th>Intento</th><th>Aciertos 1.er intento</th><th>Respuestas enviadas</th><th>Puntaje</th><th>Puntos</th></tr></thead>
            <tbody>
              @for (a of attempts(); track a.attempt_id) {
                <tr>
                  <td>{{ a.started_at | date: 'd MMM, h:mm a' }}</td>
                  <td>{{ a.activity_title }}</td>
                  <td>{{ typeLabels[a.activity_type] }}</td>
                  <td>#{{ a.attempt_number }}</td>
                  <td>{{ a.correct_first_try ?? '—' }} / {{ a.total_questions }}</td>
                  <td>{{ a.total_tries }}</td>
                  <td>@if (a.status === 'completed') { {{ a.score | number: '1.0-0' }}% } @else { <span class="chip chip-muted">Sin terminar</span> }</td>
                  <td>{{ a.points_awarded }}</td>
                </tr>
              } @empty { <tr><td colspan="8" class="muted">Sin actividades todavía.</td></tr> }
            </tbody>
          </table>
        </div>
      </section>

      <div class="grid-2">
        <section class="panel">
          <h2>Lecturas realizadas</h2>
          <ul class="plain">
            @for (r of readings(); track r.session_id) { <li>{{ r.cover_emoji }} {{ r.reading_title }} <span class="muted">· {{ r.completed_at | date: 'd MMM y' }}</span></li> }
            @empty { <li class="muted">Sin lecturas completadas.</li> }
          </ul>
        </section>
        <section class="panel">
          <h2>Insignias</h2>
          <div class="badges">
            @for (b of badges(); track b.badge.id) {
              <span class="badge" [class.off]="!b.earned" [title]="b.badge.description">{{ b.badge.icon }}<small>{{ b.badge.name }}</small></span>
            }
          </div>
        </section>
      </div>
    } @else { <div class="spinner"></div> }
  `,
  styles: `
    .back { display: inline-block; margin-bottom: 1rem; font-weight: 700; text-decoration: none; }
    .head { display: flex; gap: 1rem; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; }
    .head > div { flex: 1; } .head h1 { margin: 0; } .head p { margin: 0; }
    .av { font-size: 2.6rem; width: 72px; height: 72px; display: grid; place-items: center; background: var(--grape-soft); border-radius: 50%; }
    .manage { display: grid; gap: 1.5rem; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); margin-bottom: 1.25rem; }
    .code { font: 600 1.8rem var(--font-display); letter-spacing: .15em; margin: .3rem 0 0; }
    .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(165px, 1fr)); gap: .75rem; margin-bottom: 1rem; }
    .kpi { background: #fff; border: 1px solid var(--line); border-radius: var(--r-md); padding: .9rem 1rem; display: grid; gap: .1rem; }
    .k { font: 600 1.7rem var(--font-display); } .k small { font-size: 1rem; color: var(--ink-soft); }
    .grid-2, section.panel { margin-bottom: 1rem; }
    .small { font-size: .85rem; }
    .plain { list-style: none; padding: 0; margin: 0; display: grid; gap: .4rem; }
    .badges { display: flex; gap: .9rem; flex-wrap: wrap; }
    .badge { display: grid; justify-items: center; font-size: 2rem; width: 92px; text-align: center; }
    .badge small { font-size: .75rem; color: var(--ink-soft); }
    .badge.off { filter: grayscale(1); opacity: .4; }
  `,
})
export class StudentReportComponent implements OnInit {
  private readonly school = inject(SchoolService);
  private readonly auth = inject(AuthService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly fb = inject(FormBuilder);

  readonly id = input.required<string>();
  readonly avatar = avatarIcon;
  readonly typeLabels = ACTIVITY_TYPE_LABELS;
  readonly skillLabels = SKILL_LABELS;
  readonly student = signal<Student | null>(null);
  readonly progress = signal<ProgressSummary | null>(null);
  readonly attempts = signal<AttemptHistoryItem[]>([]);
  readonly readings = signal<ReadingHistoryItem[]>([]);
  readonly badges = signal<StudentBadge[]>([]);
  readonly classrooms = signal<Classroom[]>([]);
  readonly manage = signal(false);
  readonly code = signal<{ code: string; expires_at: string } | null>(null);

  readonly canLink = computed(() => this.auth.role() === 'teacher' || this.auth.role() === 'admin');
  readonly canChangeClassroom = computed(() => this.canLink() && this.classrooms().length > 0);
  readonly backLink = computed(() => (this.auth.role() === 'admin' ? '/admin/usuarios' : '/panel'));

  readonly editForm = this.fb.group({
    display_name: ['', [Validators.required, Validators.minLength(2)]],
    age: [null as number | null, [Validators.min(4), Validators.max(12)]],
    classroom_id: [null as number | null],
  });
  readonly pwForm = this.fb.nonNullable.group({ new_password: ['', [Validators.required, Validators.minLength(6)]] });

  ngOnInit(): void {
    const id = Number(this.id());
    forkJoin({
      student: this.school.student(id), progress: this.school.progress(id), attempts: this.school.attempts(id),
      readings: this.school.readings(id), badges: this.school.badges(id),
    }).subscribe((r) => {
      this.student.set(r.student);
      this.progress.set(r.progress);
      this.attempts.set(r.attempts);
      this.readings.set(r.readings);
      this.badges.set(r.badges);
      this.editForm.patchValue({ display_name: r.student.display_name, age: r.student.age, classroom_id: r.student.classroom_id });
    });
    if (this.canLink()) this.school.classrooms().subscribe((c) => this.classrooms.set(c));
  }

  save(): void {
    const v = this.editForm.getRawValue();
    const body: Record<string, unknown> = { display_name: v.display_name, age: v.age || null };
    if (this.canChangeClassroom() && v.classroom_id) body['classroom_id'] = v.classroom_id;
    this.school.updateStudent(this.student()!.id, body).subscribe({
      next: (s) => { this.student.set(s); this.toast.success('Datos actualizados.'); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }

  resetPassword(): void {
    this.school.resetStudentPassword(this.student()!.id, this.pwForm.getRawValue().new_password).subscribe({
      next: (m) => { this.toast.success(m.message); this.pwForm.reset(); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }

  linkCode(): void {
    this.school.linkCode(this.student()!.id).subscribe({ next: (c) => this.code.set(c), error: (err) => this.toast.error(errorMessage(err)) });
  }

  async toggleActive(s: Student): Promise<void> {
    if (s.is_active && !(await this.confirm.ask('Desactivar cuenta', `${s.display_name} no podrá ingresar hasta que la reactives. Su historial se conserva.`, 'Desactivar'))) return;
    this.school.updateStudent(s.id, { is_active: !s.is_active }).subscribe({
      next: (updated) => { this.student.set(updated); this.toast.success(updated.is_active ? 'Cuenta reactivada.' : 'Cuenta desactivada.'); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }
}
