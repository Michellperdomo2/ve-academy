import { Component, inject, signal } from '@angular/core';
import { AbstractControl, FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { switchMap } from 'rxjs';

import { errorMessage } from '../../core/interceptors/interceptors';
import { AuthService } from '../../core/services/auth.service';

export function strongPassword(control: AbstractControl): ValidationErrors | null {
  const v = String(control.value ?? '');
  return v.length >= 8 && /[A-Za-z]/.test(v) && /\d/.test(v) ? null : { weak: true };
}

@Component({
  selector: 've-register',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <section class="card">
      <h1>Crea tu cuenta</h1>
      <p class="muted">Para docentes y acudientes. Después podrás crear las cuentas de los niños.</p>
      @if (error()) { <p class="alert" role="alert">{{ error() }}</p> }
      <form class="form" [formGroup]="form" (ngSubmit)="submit()" novalidate>
        <fieldset class="roles">
          <legend>Soy</legend>
          <label [class.on]="form.value.role === 'teacher'"><input type="radio" formControlName="role" value="teacher" /> 👩‍🏫 Docente</label>
          <label [class.on]="form.value.role === 'guardian'"><input type="radio" formControlName="role" value="guardian" /> 🏡 Acudiente</label>
        </fieldset>
        <div class="field">
          <label for="full_name">Nombre completo</label>
          <input id="full_name" formControlName="full_name" autocomplete="name" />
        </div>
        <div class="field">
          <label for="email">Correo</label>
          <input id="email" type="email" formControlName="email" autocomplete="email" />
          @if (form.controls.email.touched && form.controls.email.invalid) { <span class="error">Escribe un correo válido.</span> }
        </div>
        <div class="field">
          <label for="username">Usuario</label>
          <input id="username" formControlName="username" autocapitalize="none" autocomplete="username" />
          <span class="hint">Minúsculas, números, punto o guion. Ejemplo: ana.gomez</span>
          @if (form.controls.username.touched && form.controls.username.invalid) { <span class="error">Usa de 3 a 40 caracteres permitidos.</span> }
        </div>
        <div class="field">
          <label for="password">Contraseña</label>
          <input id="password" type="password" formControlName="password" autocomplete="new-password" />
          <span class="hint">Mínimo 8 caracteres, con letras y números.</span>
          @if (form.controls.password.touched && form.controls.password.invalid) { <span class="error">La contraseña es muy débil.</span> }
        </div>
        <label class="check">
          <input type="checkbox" formControlName="accept_terms" />
          <span>Autorizo el tratamiento de mis datos y los de los menores a mi cargo con fines exclusivamente educativos (Ley 1581 de 2012).</span>
        </label>
        <button class="btn" type="submit" [disabled]="form.invalid || loading()">{{ loading() ? 'Creando…' : 'Crear cuenta' }}</button>
      </form>
      <p class="muted back">¿Ya tienes cuenta? <a routerLink="/ingresar">Ingresa</a></p>
    </section>
  `,
  styles: `
    .card { width: min(100%, 480px); }
    .roles { border: 0; padding: 0; margin: 0; display: flex; gap: .75rem; }
    .roles legend { font-weight: 700; margin-bottom: .4rem; }
    .roles label { flex: 1; display: flex; gap: .5rem; align-items: center; padding: .75rem; border: 2px solid var(--line); border-radius: var(--r-sm); cursor: pointer; font-weight: 700; }
    .roles label.on { border-color: var(--grape); background: var(--grape-soft); }
    .back { margin-top: 1rem; }
  `,
})
export class RegisterComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly form = inject(FormBuilder).nonNullable.group({
    role: ['guardian' as 'teacher' | 'guardian', Validators.required],
    full_name: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.required, Validators.email]],
    username: ['', [Validators.required, Validators.pattern(/^[a-z0-9._-]{3,40}$/)]],
    password: ['', [Validators.required, strongPassword]],
    accept_terms: [false, Validators.requiredTrue],
  });
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  submit(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.loading.set(true);
    this.error.set(null);
    const data = this.form.getRawValue();
    this.auth.register(data).pipe(switchMap(() => this.auth.login(data.username, data.password))).subscribe({
      next: (res) => this.router.navigateByUrl(this.auth.homeFor(res.user.role)),
      error: (err) => { this.error.set(errorMessage(err)); this.loading.set(false); },
    });
  }
}
