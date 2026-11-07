import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { Category } from '../../core/models/api.models';
import { errorMessage } from '../../core/interceptors/interceptors';
import { ContentService } from '../../core/services/api.services';
import { ConfirmService, ToastService } from '../../core/services/ui.services';

@Component({
  selector: 've-categories-admin',
  imports: [ReactiveFormsModule],
  template: `
    <h1>Categorías de lecturas</h1>
    <div class="grid-2">
      <section class="panel">
        <h2>{{ editing() ? 'Editar categoría' : 'Nueva categoría' }}</h2>
        <form class="form" [formGroup]="form" (ngSubmit)="save()">
          <div class="form-row">
            <div class="field"><label for="n">Nombre</label><input id="n" formControlName="name" /></div>
            <div class="field"><label for="i">Ícono (emoji)</label><input id="i" formControlName="icon" /></div>
          </div>
          <div class="field"><label for="d">Descripción</label><input id="d" formControlName="description" /></div>
          <div class="row">
            <button class="btn" type="submit" [disabled]="form.invalid">Guardar categoría</button>
            @if (editing()) { <button class="btn btn-ghost" type="button" (click)="cancel()">Cancelar</button> }
          </div>
        </form>
      </section>
      <section class="panel">
        <table class="data">
          <thead><tr><th>Categoría</th><th>Descripción</th><th></th></tr></thead>
          <tbody>
            @for (c of categories(); track c.id) {
              <tr>
                <td>{{ c.icon }} <strong>{{ c.name }}</strong></td><td>{{ c.description ?? '—' }}</td>
                <td class="right">
                  <button class="btn btn-ghost btn-sm" type="button" (click)="edit(c)">Editar</button>
                  <button class="btn btn-ghost btn-sm" type="button" (click)="remove(c)">Eliminar</button>
                </td>
              </tr>
            }
          </tbody>
        </table>
      </section>
    </div>
  `,
  styles: `.row { display: flex; gap: .5rem; } .right { text-align: right; white-space: nowrap; }`,
})
export class CategoriesAdminComponent implements OnInit {
  private readonly content = inject(ContentService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  readonly categories = signal<Category[]>([]);
  readonly editing = signal<Category | null>(null);
  readonly form = inject(FormBuilder).nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]], icon: [''], description: [''],
  });

  ngOnInit(): void { this.load(); }

  edit(c: Category): void { this.editing.set(c); this.form.setValue({ name: c.name, icon: c.icon ?? '', description: c.description ?? '' }); }
  cancel(): void { this.editing.set(null); this.form.reset(); }

  save(): void {
    const v = this.form.getRawValue();
    const body = { name: v.name, icon: v.icon || null, description: v.description || null };
    const current = this.editing();
    (current ? this.content.updateCategory(current.id, body) : this.content.createCategory(body)).subscribe({
      next: () => { this.toast.success('Categoría guardada.'); this.cancel(); this.load(); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }

  async remove(c: Category): Promise<void> {
    if (!(await this.confirm.ask('Eliminar categoría', `¿Eliminar «${c.name}»? Solo es posible si no tiene lecturas.`, 'Eliminar'))) return;
    this.content.deleteCategory(c.id).subscribe({
      next: () => { this.toast.success('Categoría eliminada.'); this.load(); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }

  private load(): void { this.content.categories().subscribe((c) => this.categories.set(c)); }
}
