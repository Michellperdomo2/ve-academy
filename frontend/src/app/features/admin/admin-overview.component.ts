import { DecimalPipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { CompanionStatus, OverviewStats } from '../../core/models/api.models';
import { ROLE_LABELS } from '../../core/models/labels';
import { AdminService } from '../../core/services/api.services';
import { SkillBarsComponent } from '../../shared/components/skill-bars.component';

@Component({
  selector: 've-admin-overview',
  imports: [DecimalPipe, RouterLink, SkillBarsComponent],
  template: `
    <h1>Resumen general</h1>
    @if (stats(); as s) {
      <section class="kpis">
        @for (role of roles; track role) {
          <a class="kpi" routerLink="/admin/usuarios" [queryParams]="{ rol: role }"><span class="k">{{ s.users_by_role[role] ?? 0 }}</span><span class="muted">{{ roleLabels[role] }}s</span></a>
        }
        <div class="kpi"><span class="k">{{ s.active_students_7d }}</span><span class="muted">Estudiantes activos (7 días)</span></div>
        <a class="kpi" routerLink="/admin/lecturas"><span class="k">{{ s.readings_published }}</span><span class="muted">Lecturas publicadas</span></a>
        <a class="kpi" routerLink="/admin/actividades"><span class="k">{{ s.activities_published }}</span><span class="muted">Actividades publicadas</span></a>
        <div class="kpi"><span class="k">{{ s.reading_sessions_completed }}</span><span class="muted">Lecturas realizadas</span></div>
        <div class="kpi"><span class="k">{{ s.attempts_completed }}</span><span class="muted">Actividades resueltas</span></div>
        <div class="kpi"><span class="k">{{ s.average_score !== null ? (s.average_score | number: '1.0-0') + '%' : '—' }}</span><span class="muted">Puntaje promedio</span></div>
      </section>
      <div class="grid-2">
        <section class="panel">
          <h2>Habilidades (todos los estudiantes)</h2>
          <ve-skill-bars [skills]="s.skills" />
        </section>
        <section class="panel">
          <h2>V&amp;E AI Companion</h2>
          <p><span class="chip chip-muted">Propuesta futura</span></p>
          <p>{{ companion()?.message }}</p>
          <p class="muted">El acompañante con IA no hace parte de los requerimientos originales. La arquitectura queda preparada
            (contratos, filtros de seguridad y endpoint de estado), pero no hay ningún servicio de IA conectado.</p>
        </section>
      </div>
    } @else { <div class="spinner"></div> }
  `,
  styles: `
    .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: .75rem; margin-bottom: 1rem; }
    .kpi { background: #fff; border: 1px solid var(--line); border-radius: var(--r-md); padding: .9rem 1rem; display: grid; text-decoration: none; color: var(--ink); }
    a.kpi:hover { border-color: var(--grape); }
    .k { font: 600 1.8rem var(--font-display); }
  `,
})
export class AdminOverviewComponent implements OnInit {
  private readonly admin = inject(AdminService);
  readonly roles = ['student', 'teacher', 'guardian', 'admin'] as const;
  readonly roleLabels = ROLE_LABELS;
  readonly stats = signal<OverviewStats | null>(null);
  readonly companion = signal<CompanionStatus | null>(null);

  ngOnInit(): void {
    this.admin.overview().subscribe((s) => this.stats.set(s));
    this.admin.companionStatus().subscribe((c) => this.companion.set(c));
  }
}
