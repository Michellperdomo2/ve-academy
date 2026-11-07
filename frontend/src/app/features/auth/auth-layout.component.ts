import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { MascotComponent } from '../../shared/components/mascot.component';

/** Marco de las páginas públicas: a la izquierda la hoja de cuaderno, a la derecha el formulario. */
@Component({
  selector: 've-auth-layout',
  imports: [RouterOutlet, MascotComponent],
  template: `
    <div class="wrap">
      <aside class="brand">
        <div class="logo"><span class="v">V</span><span class="amp">&amp;</span><span class="e">E</span> Academy</div>
        <div class="notebook motto">
          <p>Cuando lees, tu imaginación se despierta y piensa.</p>
        </div>
        <span class="mascot-disc"><ve-mascot [size]="130" /></span>
        <p class="about">Lecturas cortas, juegos de sílabas y retos para aprender a leer y comprender en primer grado.</p>
      </aside>
      <main class="content"><router-outlet /></main>
    </div>
  `,
  styles: `
    .wrap { min-height: 100vh; display: grid; grid-template-columns: minmax(300px, 0.9fr) 1.1fr; }
    .brand { background: var(--grape); color: #fff; padding: 2.5rem; display: flex; flex-direction: column; gap: 1.5rem; align-items: flex-start; justify-content: center; }
    .logo { font: 600 1.6rem var(--font-display); letter-spacing: .01em; }
    .v { color: var(--sun); } .amp { color: #fff; opacity: .7; margin: 0 .05em; } .e { color: #ffd6d7; }
    .motto { color: var(--ink); font-size: 1.5rem; max-width: 420px; transform: rotate(-1.5deg); }
    .motto p { margin: 0; }
    .about { max-width: 380px; opacity: .92; }
    .mascot-disc { display: grid; place-items: center; width: 170px; height: 170px; border-radius: 50%; background: var(--paper); }
    .content { display: grid; place-items: center; padding: 2rem 1rem; }
    @media (max-width: 820px) {
      .wrap { grid-template-columns: 1fr; }
      .brand { padding: 1.5rem 1rem; flex-direction: row; flex-wrap: wrap; align-items: center; gap: 1rem; }
      .motto, .about, .mascot-disc { display: none; }
    }
  `,
})
export class AuthLayoutComponent {}
