import { Component, inject, input, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { errorMessage } from '../../core/interceptors/interceptors';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 've-login',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <section class="card">
      <h1>¡Hola! Vamos a leer</h1>
      <p class="muted">Escribe tu usuario y tu contraseña.</p>
      @if (expirada()) { <p class="alert alert-info">Tu sesión terminó. Vuelve a ingresar.</p> }
      @if (error()) { <p class="alert" role="alert">{{ error() }}</p> }

      <form class="form" [formGroup]="form" (ngSubmit)="submit()" novalidate>
        <div class="field">
          <label for="username">Usuario o correo</label>
          <input id="username" formControlName="username" autocomplete="username" autocapitalize="none" />
        </div>
        <div class="field">
          <label for="password">Contraseña</label>
          <div class="pw">
            <input id="password" [type]="show() ? 'text' : 'password'" formControlName="password" autocomplete="current-password" />
            <button type="button" class="icon-btn" (click)="show.set(!show())" [attr.aria-label]="show() ? 'Ocultar contraseña' : 'Mostrar contraseña'">
              {{ show() ? '🙈' : '👁️' }}
            </button>
          </div>
        </div>
        <button class="btn big" type="submit" [disabled]="form.invalid || loading()">
          {{ loading() ? 'Entrando…' : 'Entrar' }}
        </button>
      </form>

      <div class="links">
        <a routerLink="/recuperar">¿Olvidaste tu contraseña?</a>
        <span>¿Eres docente o acudiente? <a routerLink="/registro">Crea tu cuenta</a></span>
      </div>
      <p class="kids muted">Los niños y niñas no se registran solos: su cuenta la crea su docente o su acudiente.</p>
    </section>
  `,
  styles: `
    .card { width: min(100%, 420px); }
    .pw { display: flex; gap: .5rem; }
    .big { min-height: 56px; font-size: 1.2rem; }
    .links { display: grid; gap: .5rem; margin-top: 1.25rem; font-size: .95rem; }
    .kids { font-size: .88rem; margin-top: 1rem; }
  `,
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly volver = input<string>();
  readonly expirada = input<string>();

  readonly form = inject(FormBuilder).nonNullable.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    password: ['', Validators.required],
  });
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly show = signal(false);

  submit(): void {
    if (this.form.invalid) return;
    this.loading.set(true);
    this.error.set(null);
    const { username, password } = this.form.getRawValue();
    this.auth.login(username.trim(), password).subscribe({
      next: (res) => {
        const target = this.volver();
        this.router.navigateByUrl(target && target.startsWith('/') ? target : this.auth.homeFor(res.user.role));
      },
      error: (err) => { this.error.set(errorMessage(err)); this.loading.set(false); },
    });
  }
}
