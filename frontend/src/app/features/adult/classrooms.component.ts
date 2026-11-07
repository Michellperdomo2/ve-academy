import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { Classroom } from '../../core/models/api.models';
import { errorMessage } from '../../core/interceptors/interceptors';
import { SchoolService } from '../../core/services/api.services';
import { ConfirmService, ToastService } from '../../core/services/ui.services';

@Component({
  selector: 've-classrooms',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="toolbar">
      <h1>Aulas</h1>
      <button class="btn" type="button" (click)="startCreate()">Nueva aula</button>
    </div>

    @if (editing() !== undefined) {
      <section class="panel form-panel">
        <h2>{{ editing() ? 'Editar aula' : 'Nueva aula' }}</h2>
        <form class="form" [formGroup]="form" (ngSubmit)="save()">
          <div class="form-row">
            <div class="field"><label for="n">Nombre</label><input id="n" formControlName="name" placeholder="Primero A" /></div>
            <div class="field"><label for="g">Grado</label><input id="g" formControlName="grade" /></div>
            <div class="field"><label for="y">Año escolar</label><input id="y" type="number" formControlName="school_year" /></div>
            <div class="field"><label for="i">Institución (opcional)</label><input id="i" formControlName="institution" /></div>
          </div>
          <div class="row-actions">
            <button class="btn" type="submit" [disabled]="form.invalid">Guardar aula</button>
            <button class="btn btn-ghost" type="button" (click)="editing.set(undefined)">Cancelar</button>
          </div>
        </form>
      </section>
    }

    <section class="panel">
      <div class="table-wrap">
        <table class="data">
          <thead><tr><th>Aula</th><th>Grado</th><th>Año</th><th>Institución</th><th>Estudiantes</th><th></th></tr></thead>
          <tbody>
            @for (c of classrooms(); track c.id) {
              <tr>
                <td><a [routerLink]="[c.id]"><strong>{{ c.name }}</strong></a></td>
                <td>{{ c.grade }}</td><td>{{ c.school_year }}</td><td>{{ c.institution ?? '—' }}</td><td>{{ c.student_count }}</td>
                <td class="right">
                  <a class="btn btn-ghost btn-sm" [routerLink]="[c.id]">Ver estadísticas</a>
                  <button class="btn btn-ghost btn-sm" type="button" (click)="startEdit(c)">Editar</button>
                  <button class="btn btn-ghost btn-sm" type="button" (click)="remove(c)">Eliminar</button>
                </td>
              </tr>
            } @empty { <tr><td colspan="6" class="muted">Aún no tienes aulas. Crea la primera para agregar estudiantes.</td></tr> }
          </tbody>
        </table>
      </div>
    </section>
  `,
  styles: `.form-panel { margin-bottom: 1rem; } .row-actions { display: flex; gap: .5rem; } .right { text-align: right; white-space: nowrap; }`,
})
export class ClassroomsComponent implements OnInit {
  private readonly school = inject(SchoolService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  readonly classrooms = signal<Classroom[]>([]);
  /** undefined = formulario cerrado; null = creando; Classroom = editando. */
  readonly editing = signal<Classroom | null | undefined>(undefined);
  readonly form = inject(FormBuilder).nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    grade: ['Primero', Validators.required],
    school_year: [new Date().getFullYear(), [Validators.required, Validators.min(2020), Validators.max(2100)]],
    institution: [''],
  });

  ngOnInit(): void { this.load(); }

  startCreate(): void { this.form.reset(); this.editing.set(null); }
  startEdit(c: Classroom): void {
    this.form.setValue({ name: c.name, grade: c.grade, school_year: c.school_year, institution: c.institution ?? '' });
    this.editing.set(c);
  }

  save(): void {
    const v = this.form.getRawValue();
    const body = { ...v, institution: v.institution || null };
    const current = this.editing();
    const req = current ? this.school.updateClassroom(current.id, body) : this.school.createClassroom(body);
    req.subscribe({
      next: () => { this.toast.success('Aula guardada.'); this.editing.set(undefined); this.load(); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }

  async remove(c: Classroom): Promise<void> {
    if (!(await this.confirm.ask('Eliminar aula', `¿Eliminar «${c.name}»? Solo es posible si no tiene estudiantes.`, 'Eliminar'))) return;
    this.school.deleteClassroom(c.id).subscribe({
      next: () => { this.toast.success('Aula eliminada.'); this.load(); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }

  private load(): void { this.school.classrooms().subscribe((c) => this.classrooms.set(c)); }
}
