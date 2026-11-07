import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ActivitySummary } from '../../core/models/api.models';
import { ACTIVITY_TYPE_LABELS, DIFFICULTY_LABELS, SKILL_LABELS } from '../../core/models/labels';
import { errorMessage } from '../../core/interceptors/interceptors';
import { ContentService } from '../../core/services/api.services';
import { ConfirmService, ToastService } from '../../core/services/ui.services';

@Component({
  selector: 've-activities-admin',
  imports: [RouterLink],
  template: `
    <div class="toolbar">
      <h1>Actividades</h1>
      <a class="btn" routerLink="nueva">Nueva actividad</a>
    </div>
    <section class="panel">
      <div class="table-wrap">
        <table class="data">
          <thead><tr><th>Actividad</th><th>Tipo</th><th>Habilidad principal</th><th>Dificultad</th><th>Preguntas</th><th>Puntos</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            @for (a of activities(); track a.id) {
              <tr>
                <td>{{ a.icon }} <strong>{{ a.title }}</strong></td>
                <td>{{ types[a.activity_type] }}</td><td>{{ skills[a.skill] }}</td><td>{{ diff[a.difficulty] }}</td>
                <td>{{ a.question_count }}</td><td>{{ a.points_reward }}</td>
                <td><span class="chip" [class.chip-ok]="a.is_published" [class.chip-muted]="!a.is_published">{{ a.is_published ? 'Publicada' : 'Borrador' }}</span></td>
                <td class="right">
                  <a class="btn btn-ghost btn-sm" [routerLink]="[a.id]">Editar</a>
                  <button class="btn btn-ghost btn-sm" type="button" (click)="remove(a)">Eliminar</button>
                </td>
              </tr>
            } @empty { <tr><td colspan="8" class="muted">No hay actividades.</td></tr> }
          </tbody>
        </table>
      </div>
    </section>
  `,
  styles: `.right { text-align: right; white-space: nowrap; }`,
})
export class ActivitiesAdminComponent implements OnInit {
  private readonly content = inject(ContentService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  readonly types = ACTIVITY_TYPE_LABELS;
  readonly skills = SKILL_LABELS;
  readonly diff = DIFFICULTY_LABELS;
  readonly activities = signal<ActivitySummary[]>([]);

  ngOnInit(): void { this.load(); }

  async remove(a: ActivitySummary): Promise<void> {
    if (!(await this.confirm.ask('Eliminar actividad', `¿Eliminar «${a.title}»? Si ya tiene intentos, despublícala en su lugar.`, 'Eliminar'))) return;
    this.content.deleteActivity(a.id).subscribe({
      next: () => { this.toast.success('Actividad eliminada.'); this.load(); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }

  private load(): void {
    this.content.activities({ include_unpublished: true, size: 100 }).subscribe((p) => this.activities.set(p.items));
  }
}
