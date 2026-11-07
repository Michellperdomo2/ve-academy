import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, input, signal } from '@angular/core';
import { FormBuilder, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { Role, User } from '../../core/models/api.models';
import { ROLE_LABELS } from '../../core/models/labels';
import { errorMessage } from '../../core/interceptors/interceptors';
import { AdminService } from '../../core/services/api.services';
import { AuthService } from '../../core/services/auth.service';
import { ConfirmService, ToastService } from '../../core/services/ui.services';
import { strongPassword } from '../auth/register.component';

@Component({
  selector: 've-users-admin',
  imports: [ReactiveFormsModule, FormsModule, DatePipe, RouterLink],
  template: `
    <div class="toolbar">
      <h1>Usuarios</h1>
      <button class="btn" type="button" (click)="showCreate.set(!showCreate())">Nuevo usuario</button>
    </div>

    @if (showCreate()) {
      <section class="panel block">
        <h2>Nuevo usuario</h2>
        <p class="muted">Para estudiantes es mejor que el docente o acudiente cree la cuenta desde su panel (queda asociada a su aula o familia).</p>
        <form class="form" [formGroup]="form" (ngSubmit)="create()">
          <div class="form-row">
            <div class="field"><label for="r">Rol</label>
              <select id="r" formControlName="role">@for (r of roleList; track r) { <option [value]="r">{{ roleLabels[r] }}</option> }</select></div>
            <div class="field"><label for="fn">Nombre completo</label><input id="fn" formControlName="full_name" /></div>
            <div class="field"><label for="un">Usuario</label><input id="un" formControlName="username" autocapitalize="none" /></div>
            <div class="field"><label for="em">Correo (opcional para estudiantes)</label><input id="em" type="email" formControlName="email" /></div>
            <div class="field"><label for="pw">Contraseña</label><input id="pw" formControlName="password" />
              <span class="hint">Mínimo 8 caracteres, con letras y números.</span></div>
          </div>
          <div><button class="btn" type="submit" [disabled]="form.invalid">Crear usuario</button></div>
        </form>
      </section>
    }

    <section class="panel">
      <div class="filters">
        <div class="field"><label for="q">Buscar</label><input id="q" [(ngModel)]="q" (keyup.enter)="go(1)" placeholder="Nombre, usuario o correo" /></div>
        <div class="field"><label for="fr">Rol</label>
          <select id="fr" [(ngModel)]="roleFilter" (change)="go(1)">
            <option value="">Todos</option>@for (r of roleList; track r) { <option [value]="r">{{ roleLabels[r] }}</option> }
          </select></div>
        <button class="btn btn-ghost" type="button" (click)="go(1)">Buscar</button>
      </div>
      <div class="table-wrap">
        <table class="data">
          <thead><tr><th>Nombre</th><th>Usuario</th><th>Correo</th><th>Rol</th><th>Estado</th><th>Último ingreso</th><th></th></tr></thead>
          <tbody>
            @for (u of users(); track u.id) {
              <tr>
                <td>{{ u.full_name }}</td><td>{{ u.username }}</td><td>{{ u.email ?? '—' }}</td>
                <td><span class="chip">{{ roleLabels[u.role] }}</span></td>
                <td><span class="chip" [class.chip-ok]="u.is_active" [class.chip-muted]="!u.is_active">{{ u.is_active ? 'Activo' : 'Inactivo' }}</span></td>
                <td>{{ u.last_login_at ? (u.last_login_at | date: 'd MMM y, h:mm a') : 'Nunca' }}</td>
                <td class="right">
                  @if (u.student_profile_id) { <a class="btn btn-ghost btn-sm" [routerLink]="['/admin/estudiantes', u.student_profile_id]">Reporte</a> }
                  <button class="btn btn-ghost btn-sm" type="button" (click)="resetTarget.set(u)">Contraseña</button>
                  @if (u.id !== auth.user()?.id) {
                    <button class="btn btn-ghost btn-sm" type="button" (click)="toggle(u)">{{ u.is_active ? 'Desactivar' : 'Activar' }}</button>
                  }
                </td>
              </tr>
            } @empty { <tr><td colspan="7" class="muted">No hay usuarios con ese filtro.</td></tr> }
          </tbody>
        </table>
      </div>
      <div class="pager">
        <button class="btn btn-ghost btn-sm" type="button" [disabled]="page() === 1" (click)="go(page() - 1)">Anterior</button>
        <span class="muted">Página {{ page() }} de {{ pages() }} · {{ total() }} usuarios</span>
        <button class="btn btn-ghost btn-sm" type="button" [disabled]="page() >= pages()" (click)="go(page() + 1)">Siguiente</button>
      </div>
    </section>

    @if (resetTarget(); as u) {
      <div class="backdrop" (click)="resetTarget.set(null)">
        <form class="dialog form" [formGroup]="pwForm" (ngSubmit)="resetPassword(u)" (click)="$event.stopPropagation()">
          <h3>Nueva contraseña para {{ u.full_name }}</h3>
          <div class="field"><label for="np">Contraseña</label><input id="np" formControlName="new_password" /></div>
          <div class="row"><button class="btn btn-ghost" type="button" (click)="resetTarget.set(null)">Cancelar</button>
            <button class="btn" type="submit" [disabled]="pwForm.invalid">Restablecer</button></div>
        </form>
      </div>
    }
  `,
  styles: `
    .block { margin-bottom: 1rem; }
    .filters { display: flex; gap: .75rem; align-items: end; flex-wrap: wrap; margin-bottom: 1rem; }
    .right { text-align: right; white-space: nowrap; }
    .pager { display: flex; gap: 1rem; align-items: center; justify-content: flex-end; margin-top: 1rem; }
    .backdrop { position: fixed; inset: 0; background: rgba(31,42,68,.45); display: grid; place-items: center; z-index: 50; padding: 1rem; }
    .dialog { background: #fff; padding: 1.5rem; border-radius: var(--r-md); width: min(420px, 100%); }
    .row { display: flex; gap: .5rem; justify-content: flex-end; }
  `,
})
export class UsersAdminComponent implements OnInit {
  private readonly admin = inject(AdminService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly fb = inject(FormBuilder);
  readonly auth = inject(AuthService);

  readonly rol = input<string>();
  readonly roleLabels = ROLE_LABELS;
  readonly roleList: Role[] = ['teacher', 'guardian', 'student', 'admin'];
  readonly users = signal<User[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pages = signal(1);
  readonly showCreate = signal(false);
  readonly resetTarget = signal<User | null>(null);
  q = '';
  roleFilter: Role | '' = '';

  readonly form = this.fb.nonNullable.group({
    role: ['teacher' as Role, Validators.required],
    full_name: ['', [Validators.required, Validators.minLength(3)]],
    username: ['', [Validators.required, Validators.pattern(/^[a-z0-9._-]{3,40}$/)]],
    email: ['', Validators.email],
    password: ['', [Validators.required, strongPassword]],
  });
  readonly pwForm = this.fb.nonNullable.group({ new_password: ['', [Validators.required, strongPassword]] });

  ngOnInit(): void {
    const r = this.rol();
    if (r && this.roleList.includes(r as Role)) this.roleFilter = r as Role;
    this.go(1);
  }

  go(page: number): void {
    this.admin.users({ role: this.roleFilter, q: this.q.trim(), page, size: 20 }).subscribe((p) => {
      this.users.set(p.items);
      this.total.set(p.total);
      this.page.set(p.page);
      this.pages.set(Math.max(1, Math.ceil(p.total / p.size)));
    });
  }

  create(): void {
    const v = this.form.getRawValue();
    this.admin.createUser({ ...v, email: v.email || null }).subscribe({
      next: () => { this.toast.success('Usuario creado.'); this.form.reset(); this.showCreate.set(false); this.go(1); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }

  async toggle(u: User): Promise<void> {
    if (u.is_active && !(await this.confirm.ask('Desactivar usuario', `${u.full_name} no podrá ingresar. Sus datos se conservan.`, 'Desactivar'))) return;
    this.admin.updateUser(u.id, { is_active: !u.is_active }).subscribe({
      next: () => { this.toast.success(u.is_active ? 'Usuario desactivado.' : 'Usuario activado.'); this.go(this.page()); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }

  resetPassword(u: User): void {
    this.admin.resetPassword(u.id, this.pwForm.getRawValue().new_password).subscribe({
      next: () => { this.toast.success('Contraseña restablecida.'); this.pwForm.reset(); this.resetTarget.set(null); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }
}
