import { Component, OnInit, inject, input, signal } from '@angular/core';
import { FormArray, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { Category, ComprehensionLevel, ReadingWrite } from '../../core/models/api.models';
import { COMPREHENSION_LABELS, DIFFICULTY_LABELS } from '../../core/models/labels';
import { errorMessage } from '../../core/interceptors/interceptors';
import { ContentService } from '../../core/services/api.services';
import { ToastService } from '../../core/services/ui.services';

/** Crear / editar lecturas. La extensión (corta, mediana, larga) la calcula el backend. */
@Component({
  selector: 've-reading-editor',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <a routerLink="/admin/lecturas" class="back">← Lecturas</a>
    <h1>{{ id() ? 'Editar lectura' : 'Nueva lectura' }}</h1>
    @if (error()) { <p class="alert" role="alert">{{ error() }}</p> }
    <form class="form" [formGroup]="form" (ngSubmit)="save()">
      <section class="panel form">
        <div class="form-row">
          <div class="field"><label for="t">Título</label><input id="t" formControlName="title" /></div>
          <div class="field"><label for="c">Temática</label>
            <select id="c" formControlName="category_id">@for (c of categories(); track c.id) { <option [ngValue]="c.id">{{ c.icon }} {{ c.name }}</option> }</select></div>
        </div>
        <div class="field"><label for="s">Resumen</label><input id="s" formControlName="summary" maxlength="300" /></div>
        <div class="form-row">
          <div class="field"><label for="d">Dificultad</label>
            <select id="d" formControlName="difficulty">@for (d of [1, 2, 3]; track d) { <option [ngValue]="d">{{ diff[d] }}</option> }</select></div>
          <div class="field"><label for="f">Tipo de comprensión</label>
            <select id="f" formControlName="comprehension_focus">@for (c of comps; track c) { <option [value]="c">{{ compLabels[c] }}</option> }</select></div>
          <div class="field"><label for="a1">Edad mínima</label><input id="a1" type="number" min="4" max="12" formControlName="min_age" /></div>
          <div class="field"><label for="a2">Edad máxima</label><input id="a2" type="number" min="4" max="12" formControlName="max_age" /></div>
          <div class="field"><label for="e">Portada (emoji)</label><input id="e" formControlName="cover_emoji" maxlength="16" /></div>
          <div class="field"><label for="col">Color de portada</label><input id="col" type="color" formControlName="cover_color" /></div>
        </div>
        <label class="check"><input type="checkbox" formControlName="is_published" /> Publicada (visible para los estudiantes)</label>
      </section>

      <section class="panel form">
        <h2>Párrafos</h2>
        <p class="muted">Frases cortas, una idea por párrafo. Puedes poner un emoji como ilustración.</p>
        <div formArrayName="paragraphs" class="stack">
          @for (p of paragraphs.controls; track p; let i = $index) {
            <div class="para" [formGroupName]="i">
              <span class="num">{{ i + 1 }}</span>
              <div class="field grow"><label [for]="'pt' + i">Texto</label><textarea [id]="'pt' + i" formControlName="text"></textarea></div>
              <div class="field ill"><label [for]="'pi' + i">Ilustración</label><input [id]="'pi' + i" formControlName="illustration" maxlength="32" /></div>
              <button class="btn btn-ghost btn-sm" type="button" (click)="removeParagraph(i)" [disabled]="paragraphs.length === 1" aria-label="Quitar párrafo">Quitar</button>
            </div>
          }
        </div>
        <div><button class="btn btn-ghost" type="button" (click)="addParagraph()">Agregar párrafo</button></div>
      </section>

      <div class="actions">
        <button class="btn" type="submit" [disabled]="form.invalid || saving()">Guardar lectura</button>
        <a class="btn btn-ghost" routerLink="/admin/lecturas">Cancelar</a>
      </div>
      @if (id()) {
        <p class="muted">Las preguntas de comprensión de esta lectura se gestionan en <a routerLink="/admin/actividades">Actividades</a> (tipo «Comprensión de textos»).</p>
      }
    </form>
  `,
  styles: `
    .back { display: inline-block; margin-bottom: 1rem; font-weight: 700; text-decoration: none; }
    .panel { margin-bottom: 1rem; }
    .para { display: flex; gap: .75rem; align-items: flex-start; flex-wrap: wrap; padding-bottom: .75rem; border-bottom: 1px dashed var(--line); }
    .num { font: 600 1.2rem var(--font-display); color: var(--margin); padding-top: 1.8rem; width: 1.5rem; }
    .grow { flex: 1 1 320px; } .ill { width: 120px; }
    .actions { display: flex; gap: .5rem; margin-bottom: 1rem; }
  `,
})
export class ReadingEditorComponent implements OnInit {
  private readonly content = inject(ContentService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);

  readonly id = input<string>();
  readonly diff = DIFFICULTY_LABELS;
  readonly comps: ComprehensionLevel[] = ['literal', 'inferential', 'critical'];
  readonly compLabels = COMPREHENSION_LABELS;
  readonly categories = signal<Category[]>([]);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    title: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(120)]],
    summary: ['', [Validators.required, Validators.minLength(2)]],
    category_id: [0, [Validators.required, Validators.min(1)]],
    difficulty: [1, Validators.required],
    min_age: [6, [Validators.required, Validators.min(4), Validators.max(12)]],
    max_age: [7, [Validators.required, Validators.min(4), Validators.max(12)]],
    comprehension_focus: ['literal' as ComprehensionLevel, Validators.required],
    cover_emoji: ['📖', Validators.required],
    cover_color: ['#ffd166', Validators.required],
    is_published: [true],
    paragraphs: this.fb.array([this.paragraphGroup()]),
  });

  get paragraphs(): FormArray { return this.form.controls.paragraphs; }

  ngOnInit(): void {
    this.content.categories().subscribe((c) => {
      this.categories.set(c);
      if (!this.id() && c.length) this.form.patchValue({ category_id: c[0].id });
    });
    const id = this.id();
    if (id) {
      this.content.reading(Number(id)).subscribe((r) => {
        this.paragraphs.clear();
        r.paragraphs.forEach((p) => this.paragraphs.push(this.paragraphGroup(p.text, p.illustration ?? '')));
        this.form.patchValue({
          title: r.title, summary: r.summary, category_id: r.category.id, difficulty: r.difficulty, min_age: r.min_age,
          max_age: r.max_age, comprehension_focus: r.comprehension_focus, cover_emoji: r.cover_emoji,
          cover_color: r.cover_color.toLowerCase(), is_published: r.is_published,
        });
      });
    }
  }

  addParagraph(): void { this.paragraphs.push(this.paragraphGroup()); }
  removeParagraph(i: number): void { this.paragraphs.removeAt(i); }

  save(): void {
    const v = this.form.getRawValue();
    const body: ReadingWrite = {
      ...v,
      paragraphs: v.paragraphs.map((p: { text: string; illustration: string }) => ({ text: p.text, illustration: p.illustration || null })),
    };
    this.saving.set(true);
    this.error.set(null);
    const id = this.id();
    (id ? this.content.updateReading(Number(id), body) : this.content.createReading(body)).subscribe({
      next: () => { this.toast.success('Lectura guardada.'); this.router.navigateByUrl('/admin/lecturas'); },
      error: (err) => { this.error.set(errorMessage(err)); this.saving.set(false); },
    });
  }

  private paragraphGroup(text = '', illustration = '') {
    return this.fb.nonNullable.group({ text: [text, Validators.required], illustration: [illustration] });
  }
}
