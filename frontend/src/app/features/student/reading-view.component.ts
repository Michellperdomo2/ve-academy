import { Component, OnDestroy, OnInit, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { ReadingCompletion, ReadingDetail } from '../../core/models/api.models';
import { COMPREHENSION_LABELS } from '../../core/models/labels';
import { ContentService, LearningService } from '../../core/services/api.services';
import { SpeechService } from '../../core/services/ui.services';
import { MascotComponent } from '../../shared/components/mascot.component';
import { StudentStateService } from './student-state.service';

/**
 * Lector: el cuento aparece sobre el cuaderno doble línea. Cada palabra se puede tocar
 * para escucharla (apoyo a la decodificación) y cada párrafo tiene botón de audio.
 */
@Component({
  selector: 've-reading-view',
  imports: [RouterLink, MascotComponent],
  template: `
    <div class="page">
      <a routerLink="/estudiante/lecturas" class="back">← Volver a la biblioteca</a>
      @if (reading(); as r) {
        <header class="head">
          <span class="cover" [style.background]="r.cover_color">{{ r.cover_emoji }}</span>
          <div>
            <h1>{{ r.title }}</h1>
            <p class="muted">{{ '⭐'.repeat(r.difficulty) }} · {{ r.category.name }} · Comprensión {{ comp[r.comprehension_focus].toLowerCase() }}</p>
          </div>
        </header>
        <p class="tip">👆 Toca una palabra para escucharla. Toca 🔊 para escuchar todo el párrafo.</p>

        <article class="notebook story">
          @for (p of r.paragraphs; track p.id) {
            <div class="para" [class.current]="current() === p.id">
              <p>
                @for (w of words(p.text); track $index) {
                  <span class="word" (click)="say(w)">{{ w }}</span>{{ ' ' }}
                }
              </p>
              <div class="side">
                @if (p.illustration) { <span class="ill" aria-hidden="true">{{ p.illustration }}</span> }
                <button class="icon-btn" type="button" (click)="readParagraph(p.id, p.text)" aria-label="Escuchar párrafo">🔊</button>
              </div>
            </div>
          }
        </article>

        @if (!result()) {
          <div class="finish">
            <button class="btn btn-sun huge" type="button" (click)="complete()" [disabled]="saving() || !sessionId()">
              ✅ Terminé de leer
            </button>
          </div>
        }

        @if (result(); as res) {
          <div class="backdrop">
            <div class="celebrate" role="dialog" aria-modal="true" aria-label="¡Terminaste la lectura!">
              <ve-mascot [size]="110" />
              <h2>{{ res.first_time ? '¡Terminaste el cuento!' : '¡Lo volviste a leer!' }}</h2>
              <p class="pts">+{{ res.points_awarded }} ⭐</p>
              @for (b of res.new_badges; track b.id) { <p class="new">🎉 Nueva insignia: {{ b.icon }} {{ b.name }}</p> }
              @for (c of res.completed_challenges; track c.id) { <p class="new">🏁 Reto cumplido: {{ c.icon }} {{ c.title }} (+{{ c.points_reward }} ⭐)</p> }
              <div class="actions">
                @if (res.next_activity_id) {
                  <a class="btn huge" [routerLink]="['/estudiante/actividades', res.next_activity_id]">📝 Responder preguntas</a>
                }
                <a class="btn btn-ghost" routerLink="/estudiante/lecturas">Elegir otro cuento</a>
              </div>
            </div>
          </div>
        }
      } @else { <div class="spinner"></div> }
    </div>
  `,
  styles: `
    .back { display: inline-block; margin-bottom: 1rem; font-weight: 700; text-decoration: none; }
    .head { display: flex; gap: 1rem; align-items: center; margin-bottom: .5rem; }
    .head h1 { margin: 0; }
    .cover { font-size: 2.6rem; width: 72px; height: 72px; border-radius: 18px; display: grid; place-items: center; flex: none; }
    .tip { color: var(--ink-soft); font-size: .95rem; }
    .story { font-size: clamp(1.35rem, 3.2vw, 1.75rem); --line-gap: 2.3em; margin-bottom: 1.5rem; }
    .para { display: flex; gap: 1rem; align-items: flex-start; border-radius: 12px; padding: 0 .3rem; }
    .para.current { background: rgba(255, 201, 60, .22); }
    .para p { flex: 1; margin: 0 0 var(--line-gap); }
    .side { display: grid; gap: .3rem; justify-items: center; padding-top: .3em; }
    .ill { font-size: 2.4rem; line-height: 1.2; }
    .word { cursor: pointer; border-radius: 6px; }
    .word:hover, .word:active { background: var(--grape-soft); }
    .finish { text-align: center; }
    .huge { min-height: 64px; font-size: 1.3rem; padding: .6em 1.6em; }
    .backdrop { position: fixed; inset: 0; background: rgba(31,42,68,.5); display: grid; place-items: center; z-index: 50; padding: 1rem; }
    .celebrate { background: #fff; border-radius: var(--r-lg); padding: 2rem; text-align: center; max-width: 440px; width: 100%; animation: pop .35s ease-out; }
    .pts { font: 600 2.6rem var(--font-display); color: var(--sun-deep); margin: .2rem 0; }
    .new { background: var(--grape-soft); border-radius: 12px; padding: .5rem; }
    .actions { display: grid; gap: .75rem; margin-top: 1rem; }
    @keyframes pop { from { transform: scale(.85); opacity: 0; } to { transform: scale(1); opacity: 1; } }
    @media (max-width: 560px) { .para { flex-direction: column; gap: 0; } .side { grid-auto-flow: column; padding: 0 0 .5rem; } }
  `,
})
export class ReadingViewComponent implements OnInit, OnDestroy {
  private readonly content = inject(ContentService);
  private readonly learning = inject(LearningService);
  private readonly speech = inject(SpeechService);
  private readonly state = inject(StudentStateService);
  private readonly router = inject(Router);

  readonly id = input.required<string>();
  readonly comp = COMPREHENSION_LABELS;
  readonly reading = signal<ReadingDetail | null>(null);
  readonly sessionId = signal<number | null>(null);
  readonly result = signal<ReadingCompletion | null>(null);
  readonly saving = signal(false);
  readonly current = signal<number | null>(null);

  ngOnInit(): void {
    const id = Number(this.id());
    this.content.reading(id).subscribe({
      next: (r) => {
        this.reading.set(r);
        this.learning.startReading(r.id).subscribe((s) => this.sessionId.set(s.id));
      },
      error: () => this.router.navigateByUrl('/estudiante/lecturas'),
    });
  }

  ngOnDestroy(): void { this.speech.stop(); }

  words(text: string): string[] { return text.split(/\s+/).filter(Boolean); }

  say(word: string): void { this.speech.speak(word.replace(/[«».,;:!¡?¿"]/g, ''), 0.7); }

  readParagraph(id: number, text: string): void {
    this.current.set(id);
    this.speech.speak(text);
  }

  complete(): void {
    const sid = this.sessionId();
    if (!sid) return;
    this.saving.set(true);
    this.speech.stop();
    this.learning.completeReading(sid).subscribe({
      next: (res) => { this.result.set(res); this.state.refresh(); },
      error: () => this.saving.set(false),
    });
  }
}
