import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ReadingSummary } from '../../core/models/api.models';
import { COMPREHENSION_LABELS, DIFFICULTY_LABELS, LENGTH_LABELS } from '../../core/models/labels';
import { errorMessage } from '../../core/interceptors/interceptors';
import { ContentService } from '../../core/services/api.services';
import { ConfirmService, ToastService } from '../../core/services/ui.services';

@Component({
  selector: 've-readings-admin',
  imports: [RouterLink],
  template: `
    <div class="toolbar">
      <h1>Lecturas</h1>
      <a class="btn" routerLink="nueva">Nueva lectura</a>
    </div>
    <section class="panel">
      <div class="table-wrap">
        <table class="data">
          <thead><tr><th>Lectura</th><th>Temática</th><th>Dificultad</th><th>Edad</th><th>Extensión</th><th>Comprensión</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            @for (r of readings(); track r.id) {
              <tr>
                <td><span class="emo">{{ r.cover_emoji }}</span> <strong>{{ r.title }}</strong></td>
                <td>{{ r.category.name }}</td><td>{{ diff[r.difficulty] }}</td><td>{{ r.min_age }}–{{ r.max_age }}</td>
                <td>{{ len[r.length] }} ({{ r.word_count }} palabras)</td><td>{{ comp[r.comprehension_focus] }}</td>
                <td><span class="chip" [class.chip-ok]="r.is_published" [class.chip-muted]="!r.is_published">{{ r.is_published ? 'Publicada' : 'Borrador' }}</span></td>
                <td class="right">
                  <a class="btn btn-ghost btn-sm" [routerLink]="[r.id]">Editar</a>
                  <button class="btn btn-ghost btn-sm" type="button" (click)="remove(r)">Eliminar</button>
                </td>
              </tr>
            } @empty { <tr><td colspan="8" class="muted">No hay lecturas.</td></tr> }
          </tbody>
        </table>
      </div>
    </section>
  `,
  styles: `.right { text-align: right; white-space: nowrap; } .emo { font-size: 1.3rem; }`,
})
export class ReadingsAdminComponent implements OnInit {
  private readonly content = inject(ContentService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  readonly diff = DIFFICULTY_LABELS;
  readonly len = LENGTH_LABELS;
  readonly comp = COMPREHENSION_LABELS;
  readonly readings = signal<ReadingSummary[]>([]);

  ngOnInit(): void { this.load(); }

  async remove(r: ReadingSummary): Promise<void> {
    if (!(await this.confirm.ask('Eliminar lectura', `¿Eliminar «${r.title}»? Si ya tiene historial de estudiantes, despublícala en su lugar.`, 'Eliminar'))) return;
    this.content.deleteReading(r.id).subscribe({
      next: () => { this.toast.success('Lectura eliminada.'); this.load(); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }

  private load(): void {
    this.content.readings({ include_unpublished: true, size: 100 }).subscribe((p) => this.readings.set(p.items));
  }
}
