import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { SkillProgress } from '../../core/models/api.models';
import { SKILL_LABELS, SKILL_STATUS_LABELS } from '../../core/models/labels';

/** Barras de precisión por habilidad (reporte visual para docentes y acudientes). */
@Component({
  selector: 've-skill-bars',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ul class="bars">
      @for (s of skills(); track s.skill) {
        <li>
          <div class="head">
            <span class="name">{{ labels[s.skill] }}</span>
            <span class="chip" [class.chip-ok]="s.status === 'strong'" [class.chip-warn]="s.status === 'developing'"
                  [class.chip-bad]="s.status === 'needs_support'" [class.chip-muted]="s.status === 'not_started'">
              {{ statusLabels[s.status] }}
            </span>
          </div>
          <div class="track" role="meter" [attr.aria-valuenow]="s.accuracy ?? 0" aria-valuemin="0" aria-valuemax="100"
               [attr.aria-label]="labels[s.skill]">
            <div class="fill" [style.width.%]="s.accuracy ?? 0" [attr.data-status]="s.status"></div>
          </div>
          <div class="meta muted">
            @if (s.answered) { {{ s.accuracy }}% de aciertos al primer intento · {{ s.answered }} {{ s.answered === 1 ? 'pregunta' : 'preguntas' }} }
            @else { Aún no ha practicado esta habilidad }
          </div>
        </li>
      }
    </ul>
  `,
  styles: `
    .bars { list-style: none; margin: 0; padding: 0; display: grid; gap: .9rem; }
    .head { display: flex; justify-content: space-between; gap: .5rem; align-items: center; margin-bottom: .25rem; }
    .name { font-weight: 700; }
    .track { height: 12px; border-radius: 999px; background: var(--rule-faint); overflow: hidden; }
    .fill { height: 100%; border-radius: inherit; background: var(--grape); }
    .fill[data-status='strong'] { background: var(--leaf); }
    .fill[data-status='needs_support'] { background: var(--margin); }
    .fill[data-status='developing'] { background: var(--sun-deep); }
    .meta { font-size: .82rem; margin-top: .2rem; }
  `,
})
export class SkillBarsComponent {
  readonly skills = input.required<SkillProgress[]>();
  readonly labels = SKILL_LABELS;
  readonly statusLabels = SKILL_STATUS_LABELS;
}
