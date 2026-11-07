import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

import { DailyActivity } from '../../core/models/api.models';

/** Actividad de los últimos 7 días: lecturas + actividades por día. */
@Component({
  selector: 've-weekly-chart',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="chart" role="img" [attr.aria-label]="summary()">
      @for (d of days(); track d.date) {
        <div class="col">
          <div class="bar-area">
            <div class="bar act" [style.height.%]="pct(d.activities)" [title]="d.activities + ' actividades'"></div>
            <div class="bar read" [style.height.%]="pct(d.readings)" [title]="d.readings + ' lecturas'"></div>
          </div>
          <span class="day">{{ dayName(d.date) }}</span>
        </div>
      }
    </div>
    <div class="legend muted"><span class="dot read"></span>Lecturas <span class="dot act"></span>Actividades</div>
  `,
  styles: `
    .chart { display: grid; grid-template-columns: repeat(7, 1fr); gap: .4rem; height: 140px; align-items: end; }
    .col { display: grid; grid-template-rows: 1fr auto; height: 100%; gap: .3rem; }
    .bar-area { display: flex; gap: 3px; align-items: flex-end; justify-content: center; border-bottom: 2px solid var(--line); }
    .bar { width: 40%; max-width: 16px; border-radius: 4px 4px 0 0; min-height: 2px; }
    .read { background: var(--grape); } .act { background: var(--sun-deep); }
    .day { text-align: center; font-size: .8rem; color: var(--ink-soft); }
    .legend { display: flex; gap: .5rem; align-items: center; font-size: .82rem; margin-top: .5rem; }
    .dot { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
  `,
})
export class WeeklyChartComponent {
  readonly days = input.required<DailyActivity[]>();
  private readonly max = computed(() => Math.max(1, ...this.days().flatMap((d) => [d.readings, d.activities])));
  readonly summary = computed(() => {
    const r = this.days().reduce((a, d) => a + d.readings, 0);
    const a = this.days().reduce((s, d) => s + d.activities, 0);
    return `Últimos 7 días: ${r} lecturas y ${a} actividades`;
  });
  pct(v: number): number { return (v / this.max()) * 100; }
  dayName(iso: string): string {
    return new Date(`${iso}T12:00:00`).toLocaleDateString('es-CO', { weekday: 'short' }).replace('.', '');
  }
}
