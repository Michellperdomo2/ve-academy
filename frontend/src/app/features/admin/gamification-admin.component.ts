import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { Badge, Challenge, Level, Skill } from '../../core/models/api.models';
import { SKILL_LABELS } from '../../core/models/labels';
import { errorMessage } from '../../core/interceptors/interceptors';
import { AdminService } from '../../core/services/api.services';
import { ToastService } from '../../core/services/ui.services';

const CHALLENGE_TYPES: Record<string, string> = {
  complete_readings: 'Completar lecturas', complete_activities: 'Completar actividades',
  perfect_scores: 'Actividades perfectas', skill_practice: 'Aciertos en una habilidad',
};
const BADGE_CRITERIA: Record<string, string> = {
  readings_completed: 'Lecturas completadas', activities_completed: 'Actividades completadas', perfect_scores: 'Actividades perfectas',
  total_points: 'Puntos acumulados', skill_correct_answers: 'Aciertos en una habilidad',
};

@Component({
  selector: 've-gamification-admin',
  imports: [ReactiveFormsModule],
  template: `
    <h1>Gamificación</h1>
    <p class="muted">Todo el progreso es individual: no existen rankings ni comparaciones entre niños.</p>

    <section class="panel block">
      <h2>Niveles</h2>
      <div class="levels">
        @for (l of levels(); track l.id) { <div class="level"><span>{{ l.icon }}</span><strong>{{ l.number }}. {{ l.name }}</strong><span class="muted">desde {{ l.min_points }} pts</span></div> }
      </div>
    </section>

    <section class="panel block">
      <h2>Insignias</h2>
      <div class="table-wrap">
        <table class="data">
          <thead><tr><th>Insignia</th><th>Criterio</th><th>Meta</th><th>Bono</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            @for (b of badges(); track b.id) {
              <tr>
                <td>{{ b.icon }} <strong>{{ b.name }}</strong><br /><span class="muted">{{ b.description }}</span></td>
                <td>{{ criteria[b.criteria_type] }} @if (b.criteria_skill) { ({{ skills[b.criteria_skill] }}) }</td>
                <td>{{ b.criteria_value }}</td><td>+{{ b.points_bonus }}</td>
                <td><span class="chip" [class.chip-ok]="b.is_active" [class.chip-muted]="!b.is_active">{{ b.is_active ? 'Activa' : 'Inactiva' }}</span></td>
                <td class="right"><button class="btn btn-ghost btn-sm" type="button" (click)="toggleBadge(b)">{{ b.is_active ? 'Desactivar' : 'Activar' }}</button></td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    </section>

    <section class="panel block">
      <h2>Retos</h2>
      <div class="table-wrap">
        <table class="data">
          <thead><tr><th>Reto</th><th>Tipo</th><th>Meta</th><th>Puntos</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            @for (c of challenges(); track c.id) {
              <tr>
                <td>{{ c.icon }} <strong>{{ c.title }}</strong><br /><span class="muted">{{ c.description }}</span></td>
                <td>{{ types[c.challenge_type] }} @if (c.skill) { ({{ skills[c.skill] }}) }</td>
                <td>{{ c.target }}</td><td>+{{ c.points_reward }}</td>
                <td><span class="chip" [class.chip-ok]="c.is_active" [class.chip-muted]="!c.is_active">{{ c.is_active ? 'Activo' : 'Inactivo' }}</span></td>
                <td class="right"><button class="btn btn-ghost btn-sm" type="button" (click)="toggleChallenge(c)">{{ c.is_active ? 'Desactivar' : 'Activar' }}</button></td>
              </tr>
            }
          </tbody>
        </table>
      </div>
      <h3>Nuevo reto</h3>
      <p class="muted">El progreso de un reto cuenta desde el momento en que se crea.</p>
      <form class="form" [formGroup]="form" (ngSubmit)="createChallenge()">
        <div class="form-row">
          <div class="field"><label for="ct">Título</label><input id="ct" formControlName="title" /></div>
          <div class="field"><label for="ci">Ícono</label><input id="ci" formControlName="icon" /></div>
          <div class="field"><label for="cty">Tipo</label>
            <select id="cty" formControlName="challenge_type">@for (t of typeKeys; track t) { <option [value]="t">{{ types[t] }}</option> }</select></div>
          @if (form.value.challenge_type === 'skill_practice') {
            <div class="field"><label for="csk">Habilidad</label>
              <select id="csk" formControlName="skill">@for (s of skillKeys; track s) { <option [value]="s">{{ skills[s] }}</option> }</select></div>
          }
          <div class="field"><label for="ctg">Meta</label><input id="ctg" type="number" min="1" formControlName="target" /></div>
          <div class="field"><label for="cp">Puntos</label><input id="cp" type="number" min="1" formControlName="points_reward" /></div>
        </div>
        <div class="field"><label for="cd">Descripción</label><input id="cd" formControlName="description" /></div>
        <div><button class="btn" type="submit" [disabled]="form.invalid">Crear reto</button></div>
      </form>
    </section>
  `,
  styles: `
    .block { margin-bottom: 1rem; }
    .levels { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: .75rem; }
    .level { display: grid; gap: .1rem; padding: .75rem; border: 1px solid var(--line); border-radius: var(--r-sm); }
    .level span:first-child { font-size: 1.8rem; }
    .right { text-align: right; }
  `,
})
export class GamificationAdminComponent implements OnInit {
  private readonly admin = inject(AdminService);
  private readonly toast = inject(ToastService);
  readonly skills = SKILL_LABELS;
  readonly skillKeys = Object.keys(SKILL_LABELS) as Skill[];
  readonly types = CHALLENGE_TYPES;
  readonly typeKeys = Object.keys(CHALLENGE_TYPES);
  readonly criteria = BADGE_CRITERIA;
  readonly levels = signal<Level[]>([]);
  readonly badges = signal<Badge[]>([]);
  readonly challenges = signal<Challenge[]>([]);
  readonly form = inject(FormBuilder).nonNullable.group({
    title: ['', [Validators.required, Validators.minLength(2)]], description: ['', [Validators.required, Validators.minLength(2)]],
    icon: ['🎯', Validators.required], challenge_type: ['complete_readings'], skill: ['phonological_awareness' as Skill],
    target: [3, [Validators.required, Validators.min(1), Validators.max(100)]], points_reward: [10, [Validators.required, Validators.min(1)]],
  });

  ngOnInit(): void {
    this.admin.levels().subscribe((l) => this.levels.set(l));
    this.loadBadges();
    this.loadChallenges();
  }

  toggleBadge(b: Badge): void {
    const { id, ...rest } = b;
    this.admin.updateBadge(id, { ...rest, is_active: !b.is_active }).subscribe({
      next: () => { this.toast.success('Insignia actualizada.'); this.loadBadges(); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }

  toggleChallenge(c: Challenge): void {
    const { id, ...rest } = c;
    this.admin.updateChallenge(id, { ...rest, is_active: !c.is_active }).subscribe({
      next: () => { this.toast.success('Reto actualizado.'); this.loadChallenges(); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }

  createChallenge(): void {
    const v = this.form.getRawValue();
    this.admin.createChallenge({ ...v, skill: v.challenge_type === 'skill_practice' ? v.skill : null, is_active: true }).subscribe({
      next: () => { this.toast.success('Reto creado.'); this.form.reset(); this.loadChallenges(); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }

  private loadBadges(): void { this.admin.badges().subscribe((b) => this.badges.set(b)); }
  private loadChallenges(): void { this.admin.challenges().subscribe((c) => this.challenges.set(c)); }
}
