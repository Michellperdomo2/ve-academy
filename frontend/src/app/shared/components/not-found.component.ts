import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { MascotComponent } from './mascot.component';

@Component({
  selector: 've-not-found',
  imports: [RouterLink, MascotComponent],
  template: `
    <main class="page empty">
      <ve-mascot [size]="140" mood="think" />
      <h1>Esta página no existe</h1>
      <p>Puede que el enlace esté incompleto.</p>
      <a class="btn" [routerLink]="auth.homeFor(auth.role())">Volver al inicio</a>
    </main>
  `,
})
export class NotFoundComponent {
  readonly auth = inject(AuthService);
}
