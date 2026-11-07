import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { ROLE_LABELS } from '../../core/models/labels';
import { AuthService } from '../../core/services/auth.service';

interface NavItem { path: string; label: string; icon: string; exact?: boolean }

/** Marco administrativo compartido por docentes, acudientes y administradores. */
@Component({
  selector: 've-adult-shell',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="layout" [class.open]="menuOpen()">
      <aside class="side">
        <div class="brand"><span class="v">V</span>&amp;<span class="e">E</span> Academy</div>
        <nav aria-label="Menú">
          @for (item of nav(); track item.path) {
            <a [routerLink]="item.path" routerLinkActive="on" [routerLinkActiveOptions]="{ exact: !!item.exact }" (click)="menuOpen.set(false)">
              <span aria-hidden="true">{{ item.icon }}</span>{{ item.label }}
            </a>
          }
        </nav>
        <div class="who">
          <strong>{{ auth.user()?.full_name }}</strong>
          <span class="muted">{{ roleLabel() }}</span>
          <button class="btn btn-ghost btn-sm" type="button" (click)="auth.logout()">Cerrar sesión</button>
        </div>
      </aside>
      <div class="main">
        <header class="mobile-bar">
          <button class="icon-btn" type="button" (click)="menuOpen.set(!menuOpen())" aria-label="Abrir menú">☰</button>
          <span class="brand"><span class="v">V</span>&amp;<span class="e">E</span> Academy</span>
        </header>
        <main class="content"><router-outlet /></main>
      </div>
    </div>
  `,
  styles: `
    .layout { display: grid; grid-template-columns: 250px 1fr; min-height: 100vh; }
    .side { position: sticky; top: 0; height: 100vh; display: flex; flex-direction: column; gap: 1.5rem; padding: 1.25rem 1rem;
      background: #fff; border-right: 1px solid var(--line); }
    .brand { font: 600 1.3rem var(--font-display); }
    .v { color: var(--grape); } .e { color: var(--margin); }
    nav { display: grid; gap: .2rem; }
    nav a { display: flex; gap: .7rem; align-items: center; padding: .6rem .75rem; border-radius: 12px; text-decoration: none; color: var(--ink); font-weight: 700; }
    nav a:hover { background: var(--paper); }
    nav a.on { background: var(--grape-soft); color: #3a2a7a; box-shadow: inset 3px 0 0 var(--grape); }
    .who { margin-top: auto; display: grid; gap: .3rem; font-size: .92rem; }
    .content { padding: 1.5rem clamp(1rem, 3vw, 2.25rem) 3rem; max-width: 1200px; }
    .mobile-bar { display: none; }
    @media (max-width: 900px) {
      .layout { grid-template-columns: 1fr; }
      .side { position: fixed; z-index: 40; width: 260px; transform: translateX(-100%); transition: transform .2s; box-shadow: 0 0 40px rgba(0,0,0,.2); }
      .layout.open .side { transform: none; }
      .mobile-bar { display: flex; gap: .75rem; align-items: center; padding: .5rem 1rem; border-bottom: 1px solid var(--line); background: #fff; position: sticky; top: 0; z-index: 30; }
    }
  `,
})
export class AdultShellComponent {
  readonly auth = inject(AuthService);
  readonly menuOpen = signal(false);
  readonly roleLabel = computed(() => (this.auth.role() ? ROLE_LABELS[this.auth.role()!] : ''));

  readonly nav = computed<NavItem[]>(() => {
    switch (this.auth.role()) {
      case 'admin':
        return [
          { path: '/admin', label: 'Resumen', icon: '📊', exact: true },
          { path: '/admin/usuarios', label: 'Usuarios', icon: '👥' },
          { path: '/admin/lecturas', label: 'Lecturas', icon: '📚' },
          { path: '/admin/actividades', label: 'Actividades', icon: '🧩' },
          { path: '/admin/categorias', label: 'Categorías', icon: '🏷️' },
          { path: '/admin/gamificacion', label: 'Gamificación', icon: '🏆' },
          { path: '/admin/perfil', label: 'Mi perfil', icon: '⚙️' },
        ];
      case 'teacher':
        return [
          { path: '/panel', label: 'Mis estudiantes', icon: '🧒', exact: true },
          { path: '/panel/aulas', label: 'Aulas', icon: '🏫' },
          { path: '/panel/perfil', label: 'Mi perfil', icon: '⚙️' },
        ];
      default:
        return [
          { path: '/panel', label: 'Mis niños', icon: '🧒', exact: true },
          { path: '/panel/perfil', label: 'Mi perfil', icon: '⚙️' },
        ];
    }
  });
}
