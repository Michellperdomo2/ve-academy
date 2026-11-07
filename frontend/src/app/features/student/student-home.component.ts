import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { StudentDashboard } from '../../core/models/api.models';
import { LearningService } from '../../core/services/api.services';
import { SpeechService } from '../../core/services/ui.services';
import { MascotComponent } from '../../shared/components/mascot.component';

@Component({
  selector: 've-student-home',
  imports: [RouterLink, MascotComponent],
  template: `
    @if (data(); as d) {
      <div class="page">
        <section class="hello">
          <ve-mascot [size]="120" />
          <div class="bubble">
            <p class="greet">{{ d.greeting }}</p>
            <p>¿Qué quieres hacer hoy?</p>
            <button class="icon-btn" type="button" (click)="speak(d.greeting + ' ¿Qué quieres hacer hoy?')" aria-label="Escuchar">🔊</button>
          </div>
        </section>

        <section class="level" aria-label="Mi nivel">
          <span class="lvl-icon">{{ d.progress.level.icon }}</span>
          <div class="lvl-body">
            <strong>Nivel {{ d.progress.level.number }}: {{ d.progress.level.name }}</strong>
            @if (d.progress.next_level; as next) {
              <div class="track"><div class="fill" [style.width.%]="levelPct(d)"></div></div>
              <span class="muted">Te faltan {{ d.progress.points_to_next_level }} ⭐ para ser {{ next.name }} {{ next.icon }}</span>
            } @else {
              <span class="muted">¡Llegaste al nivel más alto!</span>
            }
          </div>
        </section>

        <div class="tiles">
          @if (d.continue_reading[0]; as r) {
            <a class="tile read" [routerLink]="['/estudiante/lecturas', r.id]" [style.--tile]="r.cover_color">
              <span class="big">{{ r.cover_emoji }}</span>
              <span class="t-label">Leer</span>
              <span class="t-title">{{ r.title }}</span>
            </a>
          } @else {
            <a class="tile read" routerLink="/estudiante/lecturas">
              <span class="big">📚</span><span class="t-label">Leer</span><span class="t-title">¡Leíste todos! Vuelve a tu favorito</span>
            </a>
          }
          @if (d.suggested_activities[0]; as a) {
            <a class="tile play" [routerLink]="['/estudiante/actividades', a.id]">
              <span class="big">{{ a.icon }}</span>
              <span class="t-label">Jugar</span>
              <span class="t-title">{{ a.title }}</span>
            </a>
          } @else {
            <a class="tile play" routerLink="/estudiante/actividades">
              <span class="big">🧩</span><span class="t-label">Jugar</span><span class="t-title">Todas las actividades</span>
            </a>
          }
        </div>

        @if (d.active_challenges.length) {
          <section>
            <h2>Mis retos</h2>
            <div class="challenges">
              @for (c of d.active_challenges; track c.id) {
                <div class="challenge">
                  <span class="c-icon">{{ c.icon }}</span>
                  <div>
                    <strong>{{ c.title }}</strong>
                    <div class="dots" [attr.aria-label]="c.progress + ' de ' + c.target">
                      @for (i of range(c.target); track i) { <span [class.done]="i < c.progress"></span> }
                    </div>
                  </div>
                  <span class="reward">+{{ c.points_reward }} ⭐</span>
                </div>
              }
            </div>
          </section>
        }

        @if (d.suggested_activities.length > 1) {
          <section>
            <h2>Para practicar</h2>
            <div class="suggest">
              @for (a of d.suggested_activities; track a.id) {
                <a [routerLink]="['/estudiante/actividades', a.id]" class="s-item">
                  <span class="s-icon">{{ a.icon }}</span><span>{{ a.title }}</span>
                </a>
              }
            </div>
          </section>
        }

        @if (d.recent_badges.length) {
          <section>
            <h2>Mis últimas insignias</h2>
            <div class="badges">
              @for (b of d.recent_badges; track b.id) { <span class="badge" [title]="b.name">{{ b.icon }}<small>{{ b.name }}</small></span> }
            </div>
          </section>
        }
      </div>
    } @else { <div class="spinner" aria-label="Cargando"></div> }
  `,
  styles: `
    .hello { display: flex; align-items: flex-end; gap: .5rem; margin-bottom: 1.25rem; }
    .bubble { position: relative; background: #fff; border: 2px solid var(--line); border-radius: 24px 24px 24px 6px; padding: 1rem 3.5rem 1rem 1.2rem; }
    .bubble p { margin: 0; } .greet { font: 600 1.5rem var(--font-display); }
    .bubble .icon-btn { position: absolute; right: .6rem; top: .6rem; }
    .level { display: flex; gap: 1rem; align-items: center; background: #fff; border-radius: var(--r-md); padding: 1rem 1.2rem; border: 2px solid var(--rule-faint); margin-bottom: 1.25rem; }
    .lvl-icon { font-size: 2.6rem; }
    .lvl-body { flex: 1; display: grid; gap: .3rem; }
    .track { height: 16px; border-radius: 999px; background: var(--rule-faint); overflow: hidden; }
    .fill { height: 100%; background: var(--leaf); border-radius: inherit; transition: width .6s ease; }
    .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin-bottom: 1.75rem; }
    .tile { --tile: var(--sun); display: grid; gap: .2rem; padding: 1.4rem; border-radius: var(--r-lg); text-decoration: none; color: var(--ink);
      background: var(--tile); box-shadow: var(--shadow-pressed); min-height: 180px; align-content: end; transition: transform .1s; }
    .tile:active { transform: translateY(3px); box-shadow: none; }
    .tile.play { --tile: #b9e8d2; }
    .big { font-size: 3.6rem; line-height: 1; }
    .t-label { font: 600 1.8rem var(--font-display); }
    .t-title { font-size: 1.05rem; }
    section { margin-bottom: 1.75rem; }
    .challenges { display: grid; gap: .75rem; }
    .challenge { display: flex; align-items: center; gap: 1rem; background: #fff; border-radius: var(--r-md); padding: .8rem 1rem; border: 2px solid var(--rule-faint); }
    .c-icon { font-size: 2rem; }
    .challenge > div { flex: 1; }
    .dots { display: flex; gap: .3rem; flex-wrap: wrap; margin-top: .3rem; }
    .dots span { width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--rule); }
    .dots span.done { background: var(--sun); border-color: var(--sun-deep); }
    .reward { font: 600 1rem var(--font-display); white-space: nowrap; }
    .suggest { display: flex; flex-wrap: wrap; gap: .6rem; }
    .s-item { display: flex; align-items: center; gap: .5rem; background: #fff; border: 2px solid var(--line); border-radius: 999px; padding: .4rem 1rem .4rem .5rem; text-decoration: none; color: var(--ink); }
    .s-icon { font-size: 1.5rem; }
    .badges { display: flex; gap: 1rem; flex-wrap: wrap; }
    .badge { display: grid; justify-items: center; font-size: 2.4rem; }
    .badge small { font-size: .8rem; color: var(--ink-soft); }
  `,
})
export class StudentHomeComponent implements OnInit {
  private readonly learning = inject(LearningService);
  private readonly speech = inject(SpeechService);
  readonly data = signal<StudentDashboard | null>(null);

  ngOnInit(): void {
    this.learning.dashboard().subscribe((d) => this.data.set(d));
  }

  levelPct(d: StudentDashboard): number {
    const p = d.progress;
    if (!p.next_level) return 100;
    const span = p.next_level.min_points - p.level.min_points;
    return Math.min(100, ((p.total_points - p.level.min_points) / span) * 100);
  }

  range(n: number): number[] { return Array.from({ length: n }, (_, i) => i); }
  speak(text: string): void { this.speech.speak(text); }
}
