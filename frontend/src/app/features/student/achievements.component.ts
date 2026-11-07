import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';

import { ProgressSummary, ReadingHistoryItem, Reward, StudentBadge, StudentChallenge } from '../../core/models/api.models';
import { errorMessage } from '../../core/interceptors/interceptors';
import { LearningService } from '../../core/services/api.services';
import { ToastService } from '../../core/services/ui.services';
import { StudentStateService } from './student-state.service';

type Tab = 'badges' | 'challenges' | 'avatars' | 'progress';

/** Logros del niño. Solo muestra su propio avance: nunca se compara con otros niños. */
@Component({
  selector: 've-achievements',
  imports: [DatePipe],
  template: `
    <div class="page">
      <h1>🏆 Mis logros</h1>
      <div class="tabs" role="tablist">
        @for (t of tabs; track t.id) {
          <button type="button" role="tab" [attr.aria-selected]="tab() === t.id" [class.on]="tab() === t.id" (click)="tab.set(t.id)">
            {{ t.icon }} {{ t.label }}
          </button>
        }
      </div>

      @switch (tab()) {
        @case ('badges') {
          <div class="badges">
            @for (b of badges(); track b.badge.id) {
              <div class="badge" [class.locked]="!b.earned">
                <span class="b-icon">{{ b.badge.icon }}</span>
                <strong>{{ b.badge.name }}</strong>
                <span class="muted">{{ b.badge.description }}</span>
                @if (!b.earned) {
                  <div class="track"><div class="fill" [style.width.%]="(b.progress / b.target) * 100"></div></div>
                  <span class="small">{{ b.progress }} / {{ b.target }}</span>
                } @else { <span class="small ok">¡Ganada el {{ b.awarded_at | date: 'd MMM' }}!</span> }
              </div>
            }
          </div>
        }
        @case ('challenges') {
          <div class="list">
            @for (c of challenges(); track c.challenge.id) {
              <div class="row" [class.complete]="c.completed">
                <span class="r-icon">{{ c.challenge.icon }}</span>
                <div class="r-body">
                  <strong>{{ c.challenge.title }}</strong>
                  <span class="muted">{{ c.challenge.description }}</span>
                  <div class="track"><div class="fill" [style.width.%]="(c.progress / c.challenge.target) * 100"></div></div>
                </div>
                <span class="r-pts">{{ c.completed ? '✔' : '+' + c.challenge.points_reward + ' ⭐' }}</span>
              </div>
            } @empty { <p class="empty">No hay retos activos por ahora.</p> }
          </div>
        }
        @case ('avatars') {
          <p class="muted">Sube de nivel para desbloquear más amigos. Toca uno para usarlo.</p>
          <div class="avatars">
            @for (r of avatars(); track r.id) {
              <button type="button" class="avatar" [class.locked]="!r.unlocked" [class.current]="state.profile()?.avatar === r.code"
                      [disabled]="!r.unlocked || saving()" (click)="choose(r)" [attr.aria-label]="r.name + (r.unlocked ? '' : ', bloqueado')">
                <span class="a-icon">{{ r.unlocked ? r.icon : '🔒' }}</span>
                <span>{{ r.name }}</span>
                @if (!r.unlocked) { <span class="small">Nivel {{ r.required_level }}</span> }
              </button>
            }
          </div>
          <h2>Mis stickers</h2>
          <div class="stickers">
            @for (r of stickers(); track r.id) {
              <span class="sticker" [class.locked]="!r.unlocked" [title]="r.unlocked ? r.name : 'Nivel ' + r.required_level">{{ r.unlocked ? r.icon : '❔' }}</span>
            }
          </div>
        }
        @case ('progress') {
          @if (progress(); as p) {
            <div class="stats">
              <div class="stat"><span>📖</span><strong>{{ p.readings_completed }}</strong> de {{ p.readings_total }} cuentos</div>
              <div class="stat"><span>🧩</span><strong>{{ p.activities_completed }}</strong> de {{ p.activities_total }} juegos</div>
              <div class="stat"><span>✅</span><strong>{{ p.correct_answers }}</strong> respuestas correctas</div>
              <div class="stat"><span>{{ p.level.icon }}</span>Nivel <strong>{{ p.level.number }}</strong></div>
            </div>
            @if (p.strengths.length) {
              <h2>¡Eres muy bueno en!</h2>
              <ul class="plain">@for (s of p.strengths; track s) { <li>💪 {{ s }}</li> }</ul>
            }
            <h2>Cuentos que leí</h2>
            <ul class="plain">
              @for (h of history(); track h.session_id) { <li>{{ h.cover_emoji }} {{ h.reading_title }} <span class="muted">· {{ h.completed_at | date: 'd MMM' }}</span></li> }
              @empty { <li class="muted">Todavía no has terminado ningún cuento.</li> }
            </ul>
          }
        }
      }
    </div>
  `,
  styles: `
    .tabs { display: flex; gap: .5rem; flex-wrap: wrap; margin-bottom: 1.25rem; }
    .tabs button { min-height: 52px; padding: .3rem 1.1rem; border-radius: 999px; border: 2px solid var(--line); background: #fff; font: 500 1.05rem var(--font-display); cursor: pointer; color: var(--ink); }
    .tabs button.on { background: var(--grape); color: #fff; border-color: var(--grape); }
    .badges { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 1rem; }
    .badge { display: grid; justify-items: center; text-align: center; gap: .25rem; background: #fff; padding: 1.1rem; border-radius: var(--r-md); border: 2px solid var(--sun); }
    .badge.locked { border-color: var(--line); }
    .badge.locked .b-icon { filter: grayscale(1); opacity: .45; }
    .b-icon { font-size: 3rem; }
    .track { width: 100%; height: 12px; border-radius: 999px; background: var(--rule-faint); overflow: hidden; }
    .fill { height: 100%; background: var(--sun-deep); border-radius: inherit; }
    .small { font-size: .85rem; } .ok { color: #13603b; font-weight: 700; }
    .list { display: grid; gap: .75rem; }
    .row { display: flex; gap: 1rem; align-items: center; background: #fff; border-radius: var(--r-md); padding: 1rem; border: 2px solid var(--line); }
    .row.complete { border-color: var(--leaf); background: var(--leaf-soft); }
    .r-icon { font-size: 2.2rem; } .r-body { flex: 1; display: grid; gap: .25rem; } .r-pts { font: 600 1.1rem var(--font-display); }
    .avatars { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: .9rem; margin-bottom: 1.5rem; }
    .avatar { display: grid; justify-items: center; gap: .2rem; padding: 1rem .5rem; border-radius: var(--r-md); border: 3px solid var(--line); background: #fff; cursor: pointer; font: 500 1rem var(--font-display); color: var(--ink); }
    .avatar.current { border-color: var(--grape); background: var(--grape-soft); }
    .avatar.locked { opacity: .6; cursor: not-allowed; }
    .a-icon { font-size: 3rem; }
    .stickers { display: flex; gap: .75rem; flex-wrap: wrap; }
    .sticker { font-size: 2.6rem; width: 72px; height: 72px; display: grid; place-items: center; background: #fff; border-radius: 50%; border: 2px dashed var(--rule); }
    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: .9rem; margin-bottom: 1.5rem; }
    .stat { background: #fff; border-radius: var(--r-md); padding: 1rem; border: 2px solid var(--rule-faint); display: grid; gap: .2rem; }
    .stat span { font-size: 2rem; } .stat strong { font: 600 1.8rem var(--font-display); }
    .plain { list-style: none; padding: 0; display: grid; gap: .5rem; font-size: 1.1rem; }
  `,
})
export class AchievementsComponent implements OnInit {
  private readonly learning = inject(LearningService);
  private readonly toast = inject(ToastService);
  readonly state = inject(StudentStateService);

  readonly tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'badges', label: 'Insignias', icon: '🏅' }, { id: 'challenges', label: 'Retos', icon: '🎯' },
    { id: 'avatars', label: 'Avatares', icon: '🦉' }, { id: 'progress', label: 'Mi avance', icon: '📈' },
  ];
  readonly tab = signal<Tab>('badges');
  readonly badges = signal<StudentBadge[]>([]);
  readonly challenges = signal<StudentChallenge[]>([]);
  readonly avatars = signal<Reward[]>([]);
  readonly stickers = signal<Reward[]>([]);
  readonly progress = signal<ProgressSummary | null>(null);
  readonly history = signal<ReadingHistoryItem[]>([]);
  readonly saving = signal(false);

  ngOnInit(): void {
    this.learning.badges().subscribe((b) => this.badges.set(b));
    this.learning.challenges().subscribe((c) => this.challenges.set(c));
    this.learning.rewards().subscribe((r) => {
      this.avatars.set(r.filter((x) => x.kind === 'avatar'));
      this.stickers.set(r.filter((x) => x.kind === 'sticker'));
    });
    this.learning.progress().subscribe((p) => this.progress.set(p));
    this.learning.readingHistory().subscribe((h) => this.history.set(h));
  }

  choose(r: Reward): void {
    this.saving.set(true);
    this.learning.setAvatar(r.code).subscribe({
      next: (p) => { this.state.profile.set(p); this.saving.set(false); this.toast.success(`¡Ahora eres ${r.name}!`); },
      error: (err) => { this.toast.error(errorMessage(err)); this.saving.set(false); },
    });
  }
}
