import { Component, OnInit, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { avatarIcon } from '../../core/models/labels';
import { AuthService } from '../../core/services/auth.service';
import { StudentStateService } from './student-state.service';

/** Marco infantil: barra superior con avatar y estrellas, navegación inferior con íconos grandes. */
@Component({
  selector: 've-student-shell',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="top">
      <a routerLink="/estudiante" class="logo" aria-label="Inicio"><span class="v">V</span>&amp;<span class="e">E</span></a>
      @if (state.profile(); as p) {
        <a routerLink="/estudiante/logros" class="me" aria-label="Mis logros">
          <span class="avatar">{{ avatar(p.avatar) }}</span>
          <span class="name">{{ p.display_name }}</span>
          <span class="stars" [attr.aria-label]="p.total_points + ' puntos'">⭐ {{ p.total_points }}</span>
        </a>
      }
      <button class="exit" type="button" (click)="auth.logout()" aria-label="Salir">🚪 <span>Salir</span></button>
    </header>
    <main class="main"><router-outlet /></main>
    <nav class="bottom" aria-label="Navegación principal">
      <a routerLink="/estudiante" routerLinkActive="on" [routerLinkActiveOptions]="{ exact: true }"><span>🏠</span>Inicio</a>
      <a routerLink="/estudiante/lecturas" routerLinkActive="on"><span>📚</span>Leer</a>
      <a routerLink="/estudiante/actividades" routerLinkActive="on"><span>🧩</span>Jugar</a>
      <a routerLink="/estudiante/logros" routerLinkActive="on"><span>🏆</span>Logros</a>
    </nav>
  `,
  styles: `
    :host { display: block; min-height: 100vh; font-size: 19px; }
    .top { position: sticky; top: 0; z-index: 10; display: flex; align-items: center; gap: 1rem; padding: .6rem 1rem;
      background: var(--paper); border-bottom: 2px solid var(--rule-faint); }
    .logo { font: 600 1.6rem var(--font-display); color: var(--ink); text-decoration: none; }
    .v { color: var(--grape); } .e { color: var(--margin); }
    .me { margin-left: auto; display: flex; align-items: center; gap: .6rem; text-decoration: none; color: var(--ink);
      background: #fff; border: 2px solid var(--line); border-radius: 999px; padding: .25rem .9rem .25rem .3rem; }
    .avatar { font-size: 1.8rem; width: 44px; height: 44px; display: grid; place-items: center; background: var(--grape-soft); border-radius: 50%; }
    .name { font-weight: 700; }
    .stars { font: 600 1.05rem var(--font-display); background: var(--sun); border-radius: 999px; padding: .1rem .6rem; }
    .exit { border: 0; background: none; font: inherit; cursor: pointer; color: var(--ink-soft); min-height: 44px; }
    .main { padding-bottom: 6.5rem; }
    .bottom { position: fixed; bottom: 0; left: 0; right: 0; z-index: 10; display: flex; justify-content: center; gap: .25rem;
      background: #fff; border-top: 2px solid var(--rule-faint); padding: .35rem .5rem calc(.35rem + env(safe-area-inset-bottom)); }
    .bottom a { flex: 0 1 140px; display: grid; justify-items: center; gap: .1rem; padding: .35rem; border-radius: 16px;
      text-decoration: none; color: var(--ink-soft); font: 500 .95rem var(--font-display); }
    .bottom a span { font-size: 1.8rem; line-height: 1; }
    .bottom a.on { background: var(--grape-soft); color: var(--grape); }
    @media (max-width: 560px) { .name, .exit span { display: none; } }
  `,
})
export class StudentShellComponent implements OnInit {
  readonly auth = inject(AuthService);
  readonly state = inject(StudentStateService);
  readonly avatar = avatarIcon;

  ngOnInit(): void {
    this.state.refresh();
  }
}
