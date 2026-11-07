import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Category, ReadingSummary } from '../../core/models/api.models';
import { DIFFICULTY_LABELS } from '../../core/models/labels';
import { ContentService } from '../../core/services/api.services';

/** Biblioteca del estudiante: filtros visuales por nivel y temática. */
@Component({
  selector: 've-readings-list',
  imports: [RouterLink],
  template: `
    <div class="page">
      <h1>📚 Mi biblioteca</h1>
      <div class="filters" role="group" aria-label="Nivel">
        <button type="button" [class.on]="difficulty() === null" (click)="setDifficulty(null)">Todos</button>
        @for (lvl of [1, 2, 3]; track lvl) {
          <button type="button" [class.on]="difficulty() === lvl" (click)="setDifficulty(lvl)">
            {{ '⭐'.repeat(lvl) }} {{ diff[lvl] }}
          </button>
        }
      </div>
      <div class="filters" role="group" aria-label="Temática">
        <button type="button" [class.on]="category() === null" (click)="setCategory(null)">Todas</button>
        @for (c of categories(); track c.id) {
          <button type="button" [class.on]="category() === c.id" (click)="setCategory(c.id)">{{ c.icon }} {{ c.name }}</button>
        }
      </div>

      @if (loading()) { <div class="spinner"></div> }
      @else if (!readings().length) { <p class="empty">No hay cuentos con ese filtro. Prueba con otro.</p> }
      @else {
        <div class="shelf">
          @for (r of readings(); track r.id) {
            <a class="book" [routerLink]="[r.id]" [style.--cover]="r.cover_color">
              <span class="spine"></span>
              <span class="emoji">{{ r.cover_emoji }}</span>
              <span class="title">{{ r.title }}</span>
              <span class="meta">{{ '⭐'.repeat(r.difficulty) }} · {{ r.category.name }}</span>
              @if (r.completed_by_me) { <span class="done" aria-label="Ya lo leíste">✔</span> }
            </a>
          }
        </div>
      }
    </div>
  `,
  styles: `
    .filters { display: flex; gap: .5rem; flex-wrap: wrap; margin-bottom: .75rem; }
    .filters button { min-height: 48px; padding: .3rem 1rem; border-radius: 999px; border: 2px solid var(--line); background: #fff;
      font: 500 1rem var(--font-display); cursor: pointer; color: var(--ink); }
    .filters button.on { background: var(--ink); color: #fff; border-color: var(--ink); }
    .shelf { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1.25rem; margin-top: 1.25rem; }
    .book { --cover: var(--sun); position: relative; display: grid; align-content: start; gap: .3rem; padding: 1.1rem 1rem 1rem 1.6rem;
      min-height: 220px; border-radius: 8px 18px 18px 8px; background: var(--cover); color: var(--ink); text-decoration: none;
      box-shadow: inset -6px 0 0 rgba(255,255,255,.35), 0 6px 0 rgba(31,42,68,.15); transition: transform .12s; }
    .book:hover { transform: translateY(-3px) rotate(-1deg); }
    .spine { position: absolute; left: 0; top: 0; bottom: 0; width: 12px; border-radius: 8px 0 0 8px; background: rgba(31,42,68,.18); }
    .emoji { font-size: 3.4rem; line-height: 1.1; }
    .title { font: 600 1.25rem var(--font-display); }
    .meta { font-size: .85rem; opacity: .8; margin-top: auto; }
    .done { position: absolute; top: .6rem; right: .6rem; width: 34px; height: 34px; display: grid; place-items: center;
      border-radius: 50%; background: var(--leaf); color: #fff; font-weight: 700; }
  `,
})
export class ReadingsListComponent implements OnInit {
  private readonly content = inject(ContentService);
  readonly diff = DIFFICULTY_LABELS;
  readonly readings = signal<ReadingSummary[]>([]);
  readonly categories = signal<Category[]>([]);
  readonly difficulty = signal<number | null>(null);
  readonly category = signal<number | null>(null);
  readonly loading = signal(true);

  ngOnInit(): void {
    this.content.categories().subscribe((c) => this.categories.set(c));
    this.load();
  }
  setDifficulty(v: number | null): void { this.difficulty.set(v); this.load(); }
  setCategory(v: number | null): void { this.category.set(v); this.load(); }

  private load(): void {
    this.loading.set(true);
    this.content.readings({ difficulty: this.difficulty(), category_id: this.category(), size: 100 }).subscribe({
      next: (p) => { this.readings.set(p.items); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }
}
