import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, OnInit, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ClassroomStats } from '../../core/models/api.models';
import { avatarIcon } from '../../core/models/labels';
import { SchoolService } from '../../core/services/api.services';
import { SkillBarsComponent } from '../../shared/components/skill-bars.component';

/** Estadísticas del aula. Se listan por nombre, sin ranking: el orden es alfabético. */
@Component({
  selector: 've-classroom-stats',
  imports: [RouterLink, DatePipe, DecimalPipe, SkillBarsComponent],
  template: `
    <a routerLink="/panel/aulas" class="back">← Aulas</a>
    @if (stats(); as s) {
      <h1>{{ s.classroom_name }}</h1>
      <p class="muted">{{ s.student_count }} estudiantes · Puntaje promedio del aula: {{ s.average_score !== null ? (s.average_score | number: '1.0-0') + '%' : 'sin datos' }}</p>
      <div class="grid-2">
        <section class="panel">
          <h2>Habilidades del grupo</h2>
          <ve-skill-bars [skills]="s.skills" />
        </section>
        <section class="panel">
          <h2>Estudiantes</h2>
          <div class="table-wrap">
            <table class="data">
              <thead><tr><th>Estudiante</th><th>Lecturas</th><th>Actividades</th><th>Promedio</th><th>Refuerzo sugerido</th><th>Última actividad</th></tr></thead>
              <tbody>
                @for (st of s.students; track st.student_id) {
                  <tr>
                    <td><a [routerLink]="['/panel/estudiantes', st.student_id]">{{ avatar(st.avatar) }} {{ st.display_name }}</a></td>
                    <td>{{ st.readings_completed }}</td>
                    <td>{{ st.activities_completed }}</td>
                    <td>{{ st.average_score !== null ? (st.average_score | number: '1.0-0') + '%' : '—' }}</td>
                    <td>@for (n of st.needs_support; track n) { <span class="chip chip-bad">{{ n }}</span> } @empty { <span class="muted">—</span> }</td>
                    <td>{{ st.last_activity_at ? (st.last_activity_at | date: 'd MMM') : 'Nunca' }}</td>
                  </tr>
                } @empty { <tr><td colspan="6" class="muted">Esta aula no tiene estudiantes.</td></tr> }
              </tbody>
            </table>
          </div>
        </section>
      </div>
    } @else { <div class="spinner"></div> }
  `,
  styles: `.back { display: inline-block; margin-bottom: 1rem; font-weight: 700; text-decoration: none; } .chip { margin: .1rem; }`,
})
export class ClassroomStatsComponent implements OnInit {
  private readonly school = inject(SchoolService);
  readonly id = input.required<string>();
  readonly avatar = avatarIcon;
  readonly stats = signal<ClassroomStats | null>(null);

  ngOnInit(): void { this.school.classroomStats(Number(this.id())).subscribe((s) => this.stats.set(s)); }
}
