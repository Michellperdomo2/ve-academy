import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ROLE_LABELS } from '../../core/models/labels';
import { errorMessage } from '../../core/interceptors/interceptors';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/ui.services';
import { strongPassword } from '../auth/register.component';

@Component({
  selector: 've-profile',
  imports: [ReactiveFormsModule],
  template: `
    <h1>Mi perfil</h1>
    <div class="grid-2">
      <section class="panel">
        <h2>Datos</h2>
        <p class="muted">Usuario: <strong>{{ auth.user()?.username }}</strong> · Rol: {{ roleLabel }}</p>
        <form class="form" [formGroup]="profile" (ngSubmit)="saveProfile()">
          <div class="field"><label for="fn">Nombre completo</label><input id="fn" formControlName="full_name" /></div>
          <div class="field"><label for="em">Correo</label><input id="em" type="email" formControlName="email" /></div>
          <div><button class="btn" type="submit" [disabled]="profile.invalid">Guardar datos</button></div>
        </form>
      </section>
      <section class="panel">
        <h2>Cambiar contraseña</h2>
        <form class="form" [formGroup]="password" (ngSubmit)="changePassword()">
          <div class="field"><label for="cp">Contraseña actual</label><input id="cp" type="password" formControlName="current_password" autocomplete="current-password" /></div>
          <div class="field"><label for="np">Nueva contraseña</label><input id="np" type="password" formControlName="new_password" autocomplete="new-password" />
            <span class="hint">Mínimo 8 caracteres, con letras y números.</span></div>
          <div><button class="btn" type="submit" [disabled]="password.invalid">Cambiar contraseña</button></div>
        </form>
      </section>
    </div>
  `,
})
export class ProfileComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly toast = inject(ToastService);
  private readonly fb = inject(FormBuilder);
  readonly roleLabel = ROLE_LABELS[this.auth.role() ?? 'guardian'];
  readonly profile = this.fb.nonNullable.group({ full_name: ['', [Validators.required, Validators.minLength(3)]], email: ['', Validators.email] });
  readonly password = this.fb.nonNullable.group({ current_password: ['', Validators.required], new_password: ['', [Validators.required, strongPassword]] });

  ngOnInit(): void {
    const u = this.auth.user();
    if (u) this.profile.setValue({ full_name: u.full_name, email: u.email ?? '' });
  }

  saveProfile(): void {
    const v = this.profile.getRawValue();
    this.auth.updateProfile({ full_name: v.full_name, ...(v.email ? { email: v.email } : {}) }).subscribe({
      next: () => this.toast.success('Datos guardados.'),
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }

  changePassword(): void {
    const v = this.password.getRawValue();
    this.auth.changePassword(v.current_password, v.new_password).subscribe({
      next: (m) => { this.toast.success(m.message); this.password.reset(); },
      error: (err) => this.toast.error(errorMessage(err)),
    });
  }
}
