import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ActivitySummary, ActivityType } from '../../core/models/api.models';
import { ACTIVITY_TYPE_LABELS } from '../../core/models/labels';
import { ContentService } from '../../core/services/api.services';

@Component({
  selector: 've-activities-list',
  imports: [RouterLink],
  template: `
    <div class="page">
      <h1>🧩 Juegos para aprender</h1>
      @if (loading()) { <div class="spinner"></div> }
      @for (group of groups(); track group.type) {
        <section>
          <h2>{{ labels[group.type] }}</h2>
          <div class="grid">
            @for (a of group.items; track a.id) {
              <a class="act" [routerLink]="[a.id]">
                <span class="icon">{{ a.icon }}</span>
                <span class="title">{{ a.title }}</span>
                <span class="stars" [attr.aria-label]="starsFor(a) + ' de 3 estrellas'">
                  @for (i of [0, 1, 2]; track i) { <span [class.lit]="i < starsFor(a)">★</span> }
                </span>
              </a>
            }
          </div>
        </section>
      }
    </div>
  `,
  styles: `
    section { margin-bottom: 1.5rem; }
    h2 { font-size: 1.25rem; color: var(--ink-soft); }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 1rem; }
    .act { display: grid; gap: .3rem; padding: 1.1rem; background: #fff; border: 2px solid var(--line); border-radius: var(--r-md);
      text-decoration: none; color: var(--ink); box-shadow: var(--shadow-pressed); }
    .act:active { transform: translateY(3px); box-shadow: none; }
    .icon { font-size: 2.6rem; }
    .title { font: 600 1.1rem var(--font-display); }
    .stars { font-size: 1.4rem; color: var(--rule-faint); letter-spacing: .1em; }
    .stars .lit { color: var(--sun-deep); }
  `,
})
export class ActivitiesListComponent implements OnInit {
  private readonly content = inject(ContentService);
  readonly labels = ACTIVITY_TYPE_LABELS;
  readonly activities = signal<ActivitySummary[]>([]);
  readonly loading = signal(true);
  readonly groups = computed(() => {
    const map = new Map<ActivityType, ActivitySummary[]>();
    for (const a of this.activities()) map.set(a.activity_type, [...(map.get(a.activity_type) ?? []), a]);
    return [...map.entries()].map(([type, items]) => ({ type, items }));
  });

  ngOnInit(): void {
    this.content.activities({ size: 100 }).subscribe({
      next: (p) => { this.activities.set(p.items); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  starsFor(a: ActivitySummary): number {
    if (a.best_score === null) return 0;
    return a.best_score === 100 ? 3 : a.best_score >= 60 ? 2 : 1;
  }
}
