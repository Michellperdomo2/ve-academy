import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { Classroom, Student } from '../../core/models/api.models';
import { avatarIcon } from '../../core/models/labels';
import { errorMessage } from '../../core/interceptors/interceptors';
import { SchoolService } from '../../core/services/api.services';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/ui.services';

/** Panel principal de docentes y acudientes: estudiantes asociados, alta y vinculación. */
@Component({
  selector: 've-students-panel',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="toolbar">
      <div>
        <h1>{{ isTeacher() ? 'Mis estudiantes' : 'Mis niños' }}</h1>
        <p class="muted">Selecciona un estudiante para ver su reporte de progreso.</p>
      </div>
      <div class="actions">
        @if (!isTeacher()) { <button class="btn btn-ghost" type="button" (click)="toggle('link')">Vincular con código</button> }
        <button class="btn" type="button" (click)="toggle('create')">{{ isTeacher() ? 'Agregar estudiante' : 'Crear cuenta de mi niño' }}</button>
      </div>
    </div>

    @if (open() === 'create') {
      <section class="panel form-panel">
        <h2>Nueva cuenta de estudiante</h2>
        <p class="muted">Solo pedimos lo necesario: un nombre corto, un usuario y una contraseña fácil de recordar. No se piden correos ni apellidos del niño.</p>
        @if (isTeacher() && !classrooms().length) {
          <p class="alert alert-info">Primero crea un aula en <a routerLink="/panel/aulas">Aulas</a>.</p>
        }
        @if (formError()) { <p class="alert" role="alert">{{ formError() }}</p> }
        <form class="form" [formGroup]="form" (ngSubmit)="create()">
          <div class="form-row">
            <div class="field"><label for="dn">Nombre para mostrar</label><input id="dn" formControlName="display_name" placeholder="Ej.: Sofía" /></div>
            <div class="field"><label for="un">Usuario</label><input id="un" formControlName="username" autocapitalize="none" placeholder="Ej.: sofia.m" />
              <span class="hint">Minúsculas, números, punto o guion.</span></div>
            <div class="field"><label for="pw">Contraseña</label><input id="pw" formControlName="password" />
              <span class="hint">Mínimo 6 caracteres. Anótala para el niño.</span></div>
            <div class="field"><label for="age">Edad (opcional)</label><input id="age" type="number" min="4" max="12" formControlName="age" /></div>
            @if (isTeacher()) {
              <div class="field"><label for="cl">Aula</label>
                <select id="cl" formControlName="classroom_id">
                  @for (c of classrooms(); track c.id) { <option [ngValue]="c.id">{{ c.name }} ({{ c.school_year }})</option> }
                </select></div>
            } @else {
              <div class="field"><label for="rel">Parentesco (opcional)</label><input id="rel" formControlName="relationship_label" placeholder="Madre, padre, abuela…" /></div>
            }
          </div>
          <div><button class="btn" type="submit" [disabled]="form.invalid || saving()">Crear cuenta</button></div>
        </form>
      </section>
    }

    @if (open() === 'link') {
      <section class="panel form-panel">
        <h2>Vincular con el código del docente</h2>
        <p class="muted">Si tu niño ya tiene cuenta en el colegio, pide a su docente un código de vinculación (válido 7 días).</p>
        <form class="form" [formGroup]="linkForm" (ngSubmit)="link()">
          <div class="form-row">
            <div class="field"><label for="code">Código</label><input id="code" formControlName="code" autocapitalize="characters" /></div>
            <div class="field"><label for="rel2">Parentesco (opcional)</label><input id="rel2" formControlName="relationship_label" /></div>
          </div>
          <div><button class="btn" type="submit" [disabled]="linkForm.invalid || saving()">Vincular</button></div>
        </form>
      </section>
    }

    @if (loading()) { <div class="spinner"></div> }
    @else if (!students().length) {
      <div class="panel empty">
        <p>Aún no tienes estudiantes asociados.</p>
        <p class="muted">{{ isTeacher() ? 'Crea un aula y agrega a tus estudiantes.' : 'Crea la cuenta de tu niño o vincúlate con el código que te dé su docente.' }}</p>
      </div>
    } @else {
      <div class="cards">
        @for (s of students(); track s.id) {
          <a class="student" [routerLink]="['estudiantes', s.id]">
            <span class="av">{{ avatar(s.avatar) }}</span>
            <div class="info">
              <strong>{{ s.display_name }}</strong>
              <span class="muted">{{ s.classroom_name ?? 'Sin aula' }} · Nivel {{ s.level_number }}</span>
              @if (!s.is_active) { <span class="chip chip-muted">Cuenta desactivada</span> }
            </div>
            <span class="pts">⭐ {{ s.total_points }}</span>
          </a>
        }
      </div>
    }
  `,
  styles: `
    .actions { display: flex; gap: .5rem; flex-wrap: wrap; }
    .form-panel { margin-bottom: 1.25rem; }
    .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem; }
    .student { display: flex; gap: .9rem; align-items: center; padding: 1rem; background: #fff; border: 1px solid var(--line); border-radius: var(--r-md); text-decoration: none; color: var(--ink); }
    .student:hover { border-color: var(--grape); }
    .av { font-size: 2.2rem; width: 56px; height: 56px; display: grid; place-items: center; background: var(--grape-soft); border-radius: 50%; flex: none; }
    .info { flex: 1; display: grid; gap: .1rem; }
    .pts { font: 600 1rem var(--font-display); }
  `,
})
export class StudentsPanelComponent implements OnInit {
  private readonly school = inject(SchoolService);
  private readonly toast = inject(ToastService);
  private readonly auth = inject(AuthService);
  private readonly fb = inject(FormBuilder);

  readonly isTeacher = computed(() => this.auth.role() === 'teacher');
  readonly avatar = avatarIcon;
  readonly students = signal<Student[]>([]);
  readonly classrooms = signal<Classroom[]>([]);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly open = signal<'create' | 'link' | null>(null);
  readonly formError = signal<string | null>(null);

  readonly form = this.fb.group({
    display_name: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(40)]],
    username: ['', [Validators.required, Validators.pattern(/^[a-z0-9._-]{3,40}$/)]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    age: [null as number | null, [Validators.min(4), Validators.max(12)]],
    classroom_id: [null as number | null],
    relationship_label: [''],
  });
  readonly linkForm = this.fb.nonNullable.group({ code: ['', [Validators.required, Validators.minLength(6)]], relationship_label: [''] });

  ngOnInit(): void {
    this.load();
    if (this.isTeacher()) {
      this.school.classrooms().subscribe((c) => {
        this.classrooms.set(c);
        if (c.length) this.form.patchValue({ classroom_id: c[0].id });
      });
    }
  }

  toggle(which: 'create' | 'link'): void { this.open.set(this.open() === which ? null : which); this.formError.set(null); }

  create(): void {
    this.saving.set(true);
    this.formError.set(null);
    const v = this.form.getRawValue();
    const body: Record<string, unknown> = { display_name: v.display_name, username: v.username, password: v.password, age: v.age || null };
    if (this.isTeacher()) body['classroom_id'] = v.classroom_id;
    else body['relationship_label'] = v.relationship_label || null;
    this.school.createStudent(body).subscribe({
      next: (s) => {
        this.toast.success(`Cuenta creada. Usuario: ${s.username}`);
        this.form.reset({ classroom_id: this.classrooms()[0]?.id ?? null });
        this.open.set(null);
        this.saving.set(false);
        this.load();
      },
      error: (err) => { this.formError.set(errorMessage(err)); this.saving.set(false); },
    });
  }

  link(): void {
    this.saving.set(true);
    const v = this.linkForm.getRawValue();
    this.school.linkStudent(v.code.trim().toUpperCase(), v.relationship_label || null).subscribe({
      next: (s) => { this.toast.success(`Ahora acompañas a ${s.display_name}.`); this.linkForm.reset(); this.open.set(null); this.saving.set(false); this.load(); },
      error: (err) => { this.toast.error(errorMessage(err)); this.saving.set(false); },
    });
  }

  private load(): void {
    this.loading.set(true);
    this.school.students().subscribe({
      next: (s) => { this.students.set(s); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }
}
