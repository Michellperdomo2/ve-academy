import { Component, OnDestroy, OnInit, computed, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { ActivityDetail, AnswerFeedback, AttemptResult, OptionPublic, QuestionPublic } from '../../core/models/api.models';
import { errorMessage } from '../../core/interceptors/interceptors';
import { LearningService, ContentService } from '../../core/services/api.services';
import { SpeechService, ToastService } from '../../core/services/ui.services';
import { MascotComponent } from '../../shared/components/mascot.component';
import { StudentStateService } from './student-state.service';

/**
 * Reproductor de actividades: una pregunta a la vez, retroalimentación inmediata,
 * pista tras el primer error y explicación positiva tras el segundo.
 */
@Component({
  selector: 've-activity-player',
  imports: [RouterLink, MascotComponent],
  template: `
    <div class="page player">
      <a routerLink="/estudiante/actividades" class="back">← Volver a los juegos</a>
      @if (activity(); as a) {
        @if (!result()) {
          <header class="head">
            <h1>{{ a.icon }} {{ a.title }}</h1>
            <div class="instr">
              <p>{{ a.instructions }}</p>
              <button class="icon-btn" type="button" (click)="speak(a.instructions)" aria-label="Escuchar instrucciones">🔊</button>
            </div>
            @if (a.reading_id) { <a class="muted" [routerLink]="['/estudiante/lecturas', a.reading_id]">📖 Volver a leer «{{ a.reading_title }}»</a> }
            <div class="progress" aria-label="Progreso">
              @for (q of a.questions; track q.id; let i = $index) {
                <span [class.done]="i < index()" [class.now]="i === index()"></span>
              }
            </div>
          </header>

          @if (question(); as q) {
            <section class="card" [attr.aria-label]="'Pregunta ' + (index() + 1) + ' de ' + a.questions.length">
              <div class="prompt">
                @if (q.prompt_illustration) { <span class="p-ill" aria-hidden="true">{{ q.prompt_illustration }}</span> }
                <h2>{{ q.prompt }}</h2>
                <button class="icon-btn" type="button" (click)="speak(q.prompt)" aria-label="Escuchar pregunta">🔊</button>
              </div>

              @if (q.question_type === 'single_choice') {
                <div class="options">
                  @for (o of q.options; track o.id) {
                    <button type="button" class="option" (click)="choose(q, o)" [disabled]="locked()"
                            [class.picked]="picked() === o.id" [class.right]="isRight(o.id)" [class.wrong]="isWrong(o.id)">
                      @if (o.illustration) { <span class="o-ill">{{ o.illustration }}</span> }
                      <span>{{ o.text }}</span>
                    </button>
                  }
                </div>
              } @else {
                <p class="muted">Toca las piezas en orden. Toca una pieza de arriba para quitarla.</p>
                <div class="answer-row" aria-label="Tu respuesta">
                  @for (o of ordered(); track o.id) {
                    <button type="button" class="piece placed" (click)="unplace(o)" [disabled]="locked()">
                      @if (o.illustration) { <span>{{ o.illustration }}</span> } {{ o.text }}
                    </button>
                  } @empty { <span class="placeholder">Aquí va tu respuesta</span> }
                </div>
                <div class="pieces">
                  @for (o of remaining(); track o.id) {
                    <button type="button" class="piece" (click)="place(o)" [disabled]="locked()">
                      @if (o.illustration) { <span>{{ o.illustration }}</span> } {{ o.text }}
                    </button>
                  }
                </div>
                @if (!feedback()) {
                  <button class="btn btn-sun check" type="button" (click)="submitOrder(q)" [disabled]="remaining().length > 0 || busy()">
                    Comprobar
                  </button>
                }
                @if (feedback()?.correct_option_ids; as ids) {
                  <p class="solution">Así va: <strong>{{ solutionText(q, ids) }}</strong></p>
                }
              }

              @if (feedback(); as f) {
                <div class="feedback" [class.good]="f.is_correct" role="status">
                  <ve-mascot [size]="70" [mood]="f.is_correct ? 'happy' : 'think'" [animate]="false" />
                  <div>
                    <strong>{{ f.message }}</strong>
                    @if (f.hint) { <p>💡 {{ f.hint }}</p> }
                    @if (f.explanation) { <p>{{ f.explanation }}</p> }
                  </div>
                </div>
                @if (!f.can_retry) {
                  <button class="btn huge next" type="button" (click)="next()" [disabled]="busy()">
                    {{ index() + 1 < a.questions.length ? 'Siguiente pregunta' : 'Ver mi resultado' }}
                  </button>
                } @else {
                  <button class="btn btn-ghost" type="button" (click)="retry()">Intentar otra vez</button>
                }
              }
            </section>
          }
        } @else {
          @if (result(); as r) {
            <section class="result">
              <ve-mascot [size]="130" />
              <div class="big-stars" [attr.aria-label]="r.stars + ' estrellas'">
                @for (i of [0, 1, 2]; track i) { <span [class.lit]="i < r.stars">★</span> }
              </div>
              <h1>{{ r.message }}</h1>
              <p class="muted">Acertaste {{ r.correct_first_try }} de {{ r.total_questions }} a la primera.</p>
              @if (r.points_awarded > 0) { <p class="pts">+{{ r.points_awarded }} ⭐</p> }
              @else { <p class="muted">Ya habías ganado estos puntos. ¡Supera tu récord para ganar más!</p> }
              @if (r.level_up; as lvl) { <p class="new">🚀 ¡Subiste al nivel {{ lvl.number }}: {{ lvl.name }} {{ lvl.icon }}!</p> }
              @for (b of r.new_badges; track b.id) { <p class="new">🎉 Nueva insignia: {{ b.icon }} {{ b.name }}</p> }
              @for (c of r.completed_challenges; track c.id) { <p class="new">🏁 Reto cumplido: {{ c.icon }} {{ c.title }}</p> }
              @if (r.recommendations.length) {
                <h2>Para practicar más</h2>
                <div class="recs">
                  @for (rec of r.recommendations; track rec.activity_id) {
                    <a class="rec" [routerLink]="['/estudiante/actividades', rec.activity_id]" (click)="restartWith(rec.activity_id)">
                      <span>{{ rec.icon }}</span> {{ rec.title }}
                    </a>
                  }
                </div>
              }
              <div class="actions">
                <button class="btn" type="button" (click)="restartWith(a.id)">🔁 Jugar otra vez</button>
                <a class="btn btn-ghost" routerLink="/estudiante/actividades">Otros juegos</a>
              </div>
            </section>
          }
        }
      } @else { <div class="spinner"></div> }
    </div>
  `,
  styles: `
    .player { max-width: 820px; }
    .back { display: inline-block; margin-bottom: 1rem; font-weight: 700; text-decoration: none; }
    .head h1 { margin-bottom: .3rem; }
    .instr { display: flex; gap: .75rem; align-items: center; } .instr p { margin: 0; flex: 1; }
    .progress { display: flex; gap: .4rem; margin: 1rem 0; }
    .progress span { flex: 1; height: 10px; border-radius: 999px; background: var(--rule-faint); }
    .progress .done { background: var(--leaf); } .progress .now { background: var(--sun); }
    .card { background: #fff; border-radius: var(--r-lg); padding: 1.5rem; border: 2px solid var(--rule-faint); }
    .prompt { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.25rem; }
    .prompt h2 { flex: 1; margin: 0; font-size: clamp(1.4rem, 3.5vw, 2rem); }
    .p-ill { font-size: 4rem; line-height: 1; }
    .options { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: .9rem; }
    .option { min-height: 84px; display: flex; gap: .6rem; align-items: center; justify-content: center; padding: .8rem;
      font: 600 1.35rem var(--font-read); color: var(--ink); background: var(--paper); border: 3px solid var(--rule); border-radius: var(--r-md);
      cursor: pointer; box-shadow: var(--shadow-pressed); transition: transform .08s; }
    .option:active:not(:disabled) { transform: translateY(3px); box-shadow: none; }
    .option:disabled { cursor: default; }
    .o-ill { font-size: 2rem; }
    .option.picked { border-color: var(--grape); }
    .option.right { background: var(--leaf-soft); border-color: var(--leaf); animation: bounce .35s; }
    .option.wrong { background: var(--coral-soft); border-color: var(--margin); animation: shake .3s; }
    .answer-row { min-height: 76px; display: flex; flex-wrap: wrap; gap: .5rem; padding: .6rem; border: 3px dashed var(--rule); border-radius: var(--r-md); align-items: center; margin-bottom: .9rem; }
    .placeholder { color: var(--ink-soft); }
    .pieces { display: flex; flex-wrap: wrap; gap: .6rem; margin-bottom: 1rem; }
    .piece { min-height: 56px; padding: .4rem 1rem; font: 600 1.25rem var(--font-read); border-radius: 14px; border: 2px solid var(--line);
      background: var(--sun); color: var(--ink); cursor: pointer; box-shadow: var(--shadow-pressed); }
    .piece.placed { background: #fff; border-color: var(--grape); }
    .check { min-height: 56px; font-size: 1.15rem; }
    .solution { margin-top: .75rem; }
    .feedback { display: flex; gap: 1rem; align-items: center; margin-top: 1.25rem; padding: 1rem; border-radius: var(--r-md); background: #fff6dc; }
    .feedback.good { background: var(--leaf-soft); }
    .feedback p { margin: .3rem 0 0; }
    .huge { min-height: 60px; font-size: 1.2rem; }
    .next { margin-top: 1rem; width: 100%; }
    .result { text-align: center; background: #fff; border-radius: var(--r-lg); padding: 2rem 1.25rem; }
    .big-stars { font-size: 3.4rem; color: var(--rule-faint); letter-spacing: .15em; }
    .big-stars .lit { color: var(--sun-deep); animation: bounce .5s; }
    .pts { font: 600 2.4rem var(--font-display); color: var(--sun-deep); margin: .3rem 0; }
    .new { background: var(--grape-soft); border-radius: 12px; padding: .5rem; max-width: 460px; margin: .5rem auto; }
    .recs { display: grid; gap: .5rem; max-width: 460px; margin: 0 auto 1rem; }
    .rec { display: flex; gap: .5rem; align-items: center; padding: .7rem 1rem; border-radius: 14px; border: 2px solid var(--line); text-decoration: none; color: var(--ink); }
    .actions { display: flex; gap: .75rem; justify-content: center; flex-wrap: wrap; margin-top: 1rem; }
    @keyframes bounce { 50% { transform: scale(1.06); } }
    @keyframes shake { 25% { transform: translateX(-5px); } 75% { transform: translateX(5px); } }
  `,
})
export class ActivityPlayerComponent implements OnInit, OnDestroy {
  private readonly content = inject(ContentService);
  private readonly learning = inject(LearningService);
  private readonly speech = inject(SpeechService);
  private readonly toast = inject(ToastService);
  private readonly state = inject(StudentStateService);
  private readonly router = inject(Router);

  readonly id = input.required<string>();
  readonly activity = signal<ActivityDetail | null>(null);
  readonly attemptId = signal<number | null>(null);
  readonly index = signal(0);
  readonly feedback = signal<AnswerFeedback | null>(null);
  readonly picked = signal<number | null>(null);
  readonly ordered = signal<OptionPublic[]>([]);
  readonly result = signal<AttemptResult | null>(null);
  readonly busy = signal(false);

  readonly question = computed<QuestionPublic | null>(() => this.activity()?.questions[this.index()] ?? null);
  readonly remaining = computed(() => {
    const used = new Set(this.ordered().map((o) => o.id));
    return (this.question()?.options ?? []).filter((o) => !used.has(o.id));
  });
  /** Bloquea las opciones mientras se envía o se muestra la retroalimentación. */
  readonly locked = computed(() => this.busy() || this.feedback() !== null);

  ngOnInit(): void { this.load(Number(this.id())); }
  ngOnDestroy(): void { this.speech.stop(); }

  private load(activityId: number): void {
    this.reset();
    this.activity.set(null);
    this.result.set(null);
    this.index.set(0);
    this.content.activity(activityId).subscribe({
      next: (a) => {
        this.activity.set(a);
        this.learning.startAttempt(a.id).subscribe((s) => this.attemptId.set(s.attempt_id));
      },
      error: () => this.router.navigateByUrl('/estudiante/actividades'),
    });
  }

  restartWith(activityId: number): void {
    this.router.navigate(['/estudiante/actividades', activityId]);
    this.load(activityId);
  }

  speak(text: string): void { this.speech.speak(text); }

  choose(q: QuestionPublic, o: OptionPublic): void {
    this.picked.set(o.id);
    this.send({ question_id: q.id, selected_option_id: o.id });
  }

  place(o: OptionPublic): void { this.ordered.update((list) => [...list, o]); }
  unplace(o: OptionPublic): void { this.ordered.update((list) => list.filter((x) => x.id !== o.id)); }
  submitOrder(q: QuestionPublic): void { this.send({ question_id: q.id, ordered_option_ids: this.ordered().map((o) => o.id) }); }

  retry(): void {
    this.feedback.set(null);
    this.picked.set(null);
    this.ordered.set([]);
  }

  isRight(id: number): boolean {
    const f = this.feedback();
    if (!f) return false;
    return (f.is_correct && this.picked() === id) || (f.correct_option_ids?.includes(id) ?? false);
  }
  isWrong(id: number): boolean {
    const f = this.feedback();
    return !!f && !f.is_correct && this.picked() === id;
  }

  solutionText(q: QuestionPublic, ids: number[]): string {
    return ids.map((id) => q.options.find((o) => o.id === id)?.text).join(' → ');
  }

  next(): void {
    const a = this.activity();
    if (!a) return;
    if (this.index() + 1 < a.questions.length) {
      this.index.update((i) => i + 1);
      this.reset();
      return;
    }
    this.busy.set(true);
    this.learning.finish(this.attemptId()!).subscribe({
      next: (r) => { this.result.set(r); this.busy.set(false); this.state.refresh(); },
      error: (err) => { this.toast.error(errorMessage(err)); this.busy.set(false); },
    });
  }

  private send(body: { question_id: number; selected_option_id?: number; ordered_option_ids?: number[] }): void {
    const attempt = this.attemptId();
    if (!attempt) return;
    this.busy.set(true);
    this.learning.answer(attempt, body).subscribe({
      next: (f) => { this.feedback.set(f); this.busy.set(false); if (f.message) this.speech.speak(f.message); },
      error: (err) => { this.toast.error(errorMessage(err)); this.busy.set(false); },
    });
  }

  private reset(): void {
    this.feedback.set(null);
    this.picked.set(null);
    this.ordered.set([]);
  }
}
