import { Component, OnInit, inject, input, signal } from '@angular/core';
import { AbstractControl, FormArray, FormBuilder, FormGroup, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { ActivityType, ActivityWrite, QuestionAdmin, QuestionType, ReadingSummary, Skill } from '../../core/models/api.models';
import { ACTIVITY_TYPE_LABELS, DIFFICULTY_LABELS, SKILL_LABELS } from '../../core/models/labels';
import { errorMessage } from '../../core/interceptors/interceptors';
import { ContentService } from '../../core/services/api.services';
import { ToastService } from '../../core/services/ui.services';

/** Valida en el cliente la misma regla que el backend: 1 correcta, o posiciones 1..n únicas. */
function questionRules(group: AbstractControl): ValidationErrors | null {
  const type = group.get('question_type')?.value as QuestionType;
  const options = (group.get('options') as FormArray).getRawValue() as { is_correct: boolean; correct_position: number | null }[];
  if (type === 'single_choice') return options.filter((o) => o.is_correct).length === 1 ? null : { oneCorrect: true };
  const positions = options.map((o) => Number(o.correct_position)).sort((a, b) => a - b);
  return positions.every((p, i) => p === i + 1) ? null : { positions: true };
}

@Component({
  selector: 've-activity-editor',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <a routerLink="/admin/actividades" class="back">← Actividades</a>
    <h1>{{ id() ? 'Editar actividad' : 'Nueva actividad' }}</h1>
    @if (hasAttempts()) {
      <p class="alert alert-info">Esta actividad ya tiene intentos de estudiantes. Puedes cambiar título, instrucciones, pistas,
        explicaciones y publicación; para cambiar preguntas u opciones crea una actividad nueva (así se conserva el historial).</p>
    }
    @if (error()) { <p class="alert" role="alert">{{ error() }}</p> }
    <form class="form" [formGroup]="form" (ngSubmit)="save()">
      <section class="panel form">
        <div class="form-row">
          <div class="field"><label for="t">Título</label><input id="t" formControlName="title" /></div>
          <div class="field"><label for="ty">Tipo</label>
            <select id="ty" formControlName="activity_type">@for (t of typeList; track t) { <option [value]="t">{{ types[t] }}</option> }</select></div>
          <div class="field"><label for="sk">Habilidad principal</label>
            <select id="sk" formControlName="skill">@for (s of skillList; track s) { <option [value]="s">{{ skills[s] }}</option> }</select></div>
          <div class="field"><label for="d">Dificultad</label>
            <select id="d" formControlName="difficulty">@for (d of [1, 2, 3]; track d) { <option [ngValue]="d">{{ diff[d] }}</option> }</select></div>
          <div class="field"><label for="ic">Ícono (emoji)</label><input id="ic" formControlName="icon" /></div>
          <div class="field"><label for="pts">Puntos</label><input id="pts" type="number" min="1" max="100" formControlName="points_reward" /></div>
          <div class="field"><label for="rd">Lectura asociada (opcional)</label>
            <select id="rd" formControlName="reading_id"><option [ngValue]="null">Ninguna</option>
              @for (r of readings(); track r.id) { <option [ngValue]="r.id">{{ r.title }}</option> }</select></div>
        </div>
        <div class="field"><label for="in">Instrucciones para el niño</label><input id="in" formControlName="instructions" /></div>
        <label class="check"><input type="checkbox" formControlName="is_published" /> Publicada</label>
      </section>

      <div formArrayName="questions" class="stack">
        @for (q of questions.controls; track q; let qi = $index) {
          <section class="panel form q" [formGroupName]="qi">
            <div class="q-head">
              <h3>Pregunta {{ qi + 1 }}</h3>
              <button class="btn btn-ghost btn-sm" type="button" (click)="questions.removeAt(qi)" [disabled]="questions.length === 1 || hasAttempts()">Quitar pregunta</button>
            </div>
            <div class="form-row">
              <div class="field grow"><label [for]="'qp' + qi">Enunciado</label><input [id]="'qp' + qi" formControlName="prompt" /></div>
              <div class="field"><label [for]="'qi' + qi">Ilustración</label><input [id]="'qi' + qi" formControlName="prompt_illustration" /></div>
              <div class="field"><label [for]="'qt' + qi">Formato</label>
                <select [id]="'qt' + qi" formControlName="question_type">
                  <option value="single_choice">Selección única</option><option value="ordering">Ordenar</option></select></div>
              <div class="field"><label [for]="'qs' + qi">Habilidad que mide</label>
                <select [id]="'qs' + qi" formControlName="skill">@for (s of skillList; track s) { <option [value]="s">{{ skills[s] }}</option> }</select></div>
            </div>
            <div class="form-row">
              <div class="field"><label [for]="'qh' + qi">Pista (tras el 1.er error)</label><input [id]="'qh' + qi" formControlName="hint" /></div>
              <div class="field"><label [for]="'qe' + qi">Explicación (tras acertar o el 2.º error)</label><input [id]="'qe' + qi" formControlName="explanation" /></div>
            </div>
            <div formArrayName="options" class="options">
              @for (o of optionsOf(qi).controls; track o; let oi = $index) {
                <div class="opt" [formGroupName]="oi">
                  <div class="field grow"><label [for]="'ot' + qi + '-' + oi">Opción {{ oi + 1 }}</label><input [id]="'ot' + qi + '-' + oi" formControlName="text" /></div>
                  <div class="field small"><label [for]="'oi' + qi + '-' + oi">Ilustración</label><input [id]="'oi' + qi + '-' + oi" formControlName="illustration" /></div>
                  @if (q.value.question_type === 'single_choice') {
                    <label class="check correct"><input type="radio" [name]="'correct' + qi" [checked]="o.value.is_correct" (change)="markCorrect(qi, oi)" /> Correcta</label>
                  } @else {
                    <div class="field small"><label [for]="'op' + qi + '-' + oi">Posición correcta</label><input [id]="'op' + qi + '-' + oi" type="number" min="1" formControlName="correct_position" /></div>
                  }
                  <button class="btn btn-ghost btn-sm" type="button" (click)="optionsOf(qi).removeAt(oi)" [disabled]="optionsOf(qi).length <= 2 || hasAttempts()">Quitar</button>
                </div>
              }
            </div>
            @if (q.errors?.['oneCorrect']) { <span class="error">Marca exactamente una opción correcta.</span> }
            @if (q.errors?.['positions']) { <span class="error">Las posiciones correctas deben ser 1, 2, 3… sin repetir.</span> }
            <div><button class="btn btn-ghost btn-sm" type="button" (click)="addOption(qi)" [disabled]="optionsOf(qi).length >= 8 || hasAttempts()">Agregar opción</button></div>
          </section>
        }
      </div>
      <div><button class="btn btn-ghost" type="button" (click)="addQuestion()" [disabled]="hasAttempts()">Agregar pregunta</button></div>
      <div class="actions">
        <button class="btn" type="submit" [disabled]="form.invalid || saving()">Guardar actividad</button>
        <a class="btn btn-ghost" routerLink="/admin/actividades">Cancelar</a>
      </div>
    </form>
  `,
  styles: `
    .back { display: inline-block; margin-bottom: 1rem; font-weight: 700; text-decoration: none; }
    .panel { margin-bottom: 1rem; }
    .q { border-left: 4px solid var(--grape); }
    .q-head { display: flex; justify-content: space-between; align-items: center; }
    .grow { flex: 2 1 260px; }
    .options { display: grid; gap: .5rem; }
    .opt { display: flex; gap: .75rem; align-items: end; flex-wrap: wrap; }
    .small { width: 140px; }
    .correct { padding-bottom: .7rem; }
    .error { color: var(--margin); font-size: .9rem; }
    .actions { display: flex; gap: .5rem; margin: 1rem 0; }
  `,
})
export class ActivityEditorComponent implements OnInit {
  private readonly content = inject(ContentService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);

  readonly id = input<string>();
  readonly types = ACTIVITY_TYPE_LABELS;
  readonly skills = SKILL_LABELS;
  readonly diff = DIFFICULTY_LABELS;
  readonly typeList = Object.keys(ACTIVITY_TYPE_LABELS) as ActivityType[];
  readonly skillList = Object.keys(SKILL_LABELS) as Skill[];
  readonly readings = signal<ReadingSummary[]>([]);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly hasAttempts = signal(false);

  readonly form = this.fb.nonNullable.group({
    title: ['', [Validators.required, Validators.minLength(2)]],
    activity_type: ['syllables' as ActivityType, Validators.required],
    skill: ['phonological_awareness' as Skill, Validators.required],
    difficulty: [1, Validators.required],
    icon: ['⭐', Validators.required],
    points_reward: [10, [Validators.required, Validators.min(1), Validators.max(100)]],
    reading_id: [null as number | null],
    instructions: ['', [Validators.required, Validators.minLength(2)]],
    is_published: [true],
    questions: this.fb.array<FormGroup>([this.questionGroup()]),
  });

  get questions(): FormArray<FormGroup> { return this.form.controls.questions; }
  optionsOf(qi: number): FormArray { return this.questions.at(qi).get('options') as FormArray; }

  ngOnInit(): void {
    this.content.readings({ include_unpublished: true, size: 100 }).subscribe((p) => this.readings.set(p.items));
    const id = this.id();
    if (!id) return;
    this.content.activityAdmin(Number(id)).subscribe((a) => {
      this.hasAttempts.set(a.attempt_count > 0);
      this.questions.clear();
      a.questions.forEach((q) => this.questions.push(this.questionGroup(q)));
      this.form.patchValue({
        title: a.title, activity_type: a.activity_type, skill: a.skill, difficulty: a.difficulty, icon: a.icon,
        points_reward: a.points_reward, reading_id: a.reading_id, instructions: a.instructions, is_published: a.is_published,
      });
    });
  }

  addQuestion(): void { this.questions.push(this.questionGroup()); }
  addOption(qi: number): void { this.optionsOf(qi).push(this.optionGroup()); }

  markCorrect(qi: number, oi: number): void {
    this.optionsOf(qi).controls.forEach((c, i) => c.patchValue({ is_correct: i === oi }));
    this.questions.at(qi).updateValueAndValidity();
  }

  save(): void {
    const v = this.form.getRawValue();
    const body: ActivityWrite = {
      ...v,
      questions: v.questions.map((q) => ({
        prompt: q['prompt'], prompt_illustration: q['prompt_illustration'] || null, question_type: q['question_type'],
        skill: q['skill'], hint: q['hint'] || null, explanation: q['explanation'],
        options: (q['options'] as { text: string; illustration: string; is_correct: boolean; correct_position: number | null }[]).map((o) => ({
          text: o.text, illustration: o.illustration || null,
          is_correct: q['question_type'] === 'single_choice' ? o.is_correct : false,
          correct_position: q['question_type'] === 'ordering' ? Number(o.correct_position) : null,
        })),
      })),
    };
    this.saving.set(true);
    this.error.set(null);
    const id = this.id();
    (id ? this.content.updateActivity(Number(id), body) : this.content.createActivity(body)).subscribe({
      next: () => { this.toast.success('Actividad guardada.'); this.router.navigateByUrl('/admin/actividades'); },
      error: (err) => {
        if (err?.status === 409) this.hasAttempts.set(true);
        this.error.set(errorMessage(err));
        this.saving.set(false);
      },
    });
  }

  private questionGroup(q?: QuestionAdmin): FormGroup {
    const options = q?.options.map((o) => this.optionGroup(o.text, o.illustration ?? '', o.is_correct, o.correct_position))
      ?? [this.optionGroup('', '', true), this.optionGroup()];
    return this.fb.nonNullable.group({
      prompt: [q?.prompt ?? '', Validators.required],
      prompt_illustration: [q?.prompt_illustration ?? ''],
      question_type: [q?.question_type ?? ('single_choice' as QuestionType)],
      skill: [q?.skill ?? ('literal' as Skill)],
      hint: [q?.hint ?? ''],
      explanation: [q?.explanation ?? '', Validators.required],
      options: this.fb.array(options),
    }, { validators: questionRules });
  }

  private optionGroup(text = '', illustration = '', isCorrect = false, position: number | null = null): FormGroup {
    return this.fb.nonNullable.group({
      text: [text, Validators.required], illustration: [illustration], is_correct: [isCorrect], correct_position: [position as number | null],
    });
  }
}
