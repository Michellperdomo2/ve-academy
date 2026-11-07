import { Component, inject, input, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { errorMessage } from '../../core/interceptors/interceptors';
import { AuthService } from '../../core/services/auth.service';
import { strongPassword } from './register.component';

@Component({
  selector: 've-reset-password',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <main class="page">
      <section class="panel card">
        <h1>Nueva contraseña</h1>
        @if (done()) {
          <p class="alert alert-ok">{{ done() }}</p>
          <a class="btn" routerLink="/ingresar">Ingresar</a>
        } @else if (!token()) {
          <p class="alert">El enlace está incompleto. Solicita uno nuevo.</p>
          <a routerLink="/recuperar">Solicitar enlace</a>
        } @else {
          @if (error()) { <p class="alert" role="alert">{{ error() }}</p> }
          <form class="form" [formGroup]="form" (ngSubmit)="submit()">
            <div class="field">
              <label for="pw">Nueva contraseña</label>
              <input id="pw" type="password" formControlName="password" autocomplete="new-password" />
              <span class="hint">Mínimo 8 caracteres, con letras y números.</span>
            </div>
            <button class="btn" type="submit" [disabled]="form.invalid || loading()">Guardar contraseña</button>
          </form>
        }
      </section>
    </main>
  `,
  styles: `.card { max-width: 440px; margin: 3rem auto; }`,
})
export class ResetPasswordComponent {
  private readonly auth = inject(AuthService);
  readonly token = input<string>();
  readonly form = inject(FormBuilder).nonNullable.group({ password: ['', [Validators.required, strongPassword]] });
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly done = signal<string | null>(null);

  submit(): void {
    this.loading.set(true);
    this.auth.confirmPasswordReset(this.token() ?? '', this.form.getRawValue().password).subscribe({
      next: (res) => this.done.set(res.message),
      error: (err) => { this.error.set(errorMessage(err)); this.loading.set(false); },
    });
  }
}
