import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { errorMessage } from '../../core/interceptors/interceptors';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 've-forgot-password',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <section class="card">
      <h1>Recupera tu contraseña</h1>
      <p class="muted">Para docentes y acudientes con correo registrado. Si eres estudiante, pide ayuda a tu docente o acudiente.</p>
      @if (message()) { <p class="alert alert-info" role="status">{{ message() }}</p> }
      @if (error()) { <p class="alert" role="alert">{{ error() }}</p> }
      <form class="form" [formGroup]="form" (ngSubmit)="submit()">
        <div class="field">
          <label for="email">Correo</label>
          <input id="email" type="email" formControlName="email" autocomplete="email" />
        </div>
        <button class="btn" type="submit" [disabled]="form.invalid || loading()">Enviar enlace</button>
      </form>
      <p class="muted back"><a routerLink="/ingresar">Volver a ingresar</a></p>
    </section>
  `,
  styles: `.card { width: min(100%, 420px); } .back { margin-top: 1rem; }`,
})
export class ForgotPasswordComponent {
  private readonly auth = inject(AuthService);
  readonly form = inject(FormBuilder).nonNullable.group({ email: ['', [Validators.required, Validators.email]] });
  readonly loading = signal(false);
  readonly message = signal<string | null>(null);
  readonly error = signal<string | null>(null);

  submit(): void {
    this.loading.set(true);
    this.auth.requestPasswordReset(this.form.getRawValue().email).subscribe({
      next: (res) => { this.message.set(res.message); this.loading.set(false); },
      error: (err) => { this.error.set(errorMessage(err)); this.loading.set(false); },
    });
  }
}
