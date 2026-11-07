import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { ConfirmService, ToastService } from '../../core/services/ui.services';

/** Muestra avisos (toasts) y el diálogo de confirmación global. */
@Component({
  selector: 've-feedback-host',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="toasts" aria-live="polite">
      @for (t of toast.toasts(); track t.id) {
        <div class="toast" [class]="'toast toast-' + t.kind" role="status">
          <span>{{ t.text }}</span>
          <button type="button" (click)="toast.dismiss(t.id)" aria-label="Cerrar aviso">✕</button>
        </div>
      }
    </div>
    @if (confirm.request(); as req) {
      <div class="backdrop" (click)="confirm.close(false)">
        <div class="dialog" role="alertdialog" aria-modal="true" [attr.aria-label]="req.title" (click)="$event.stopPropagation()">
          <h3>{{ req.title }}</h3>
          <p>{{ req.text }}</p>
          <div class="actions">
            <button class="btn btn-ghost" type="button" (click)="confirm.close(false)">Cancelar</button>
            <button class="btn btn-danger" type="button" (click)="confirm.close(true)">{{ req.confirmLabel }}</button>
          </div>
        </div>
      </div>
    }
  `,
  styles: `
    .toasts { position: fixed; bottom: 1rem; left: 50%; transform: translateX(-50%); display: grid; gap: .5rem; z-index: 1000; width: min(92vw, 460px); }
    .toast { display: flex; gap: .75rem; align-items: center; justify-content: space-between; padding: .75rem 1rem;
      border-radius: 14px; background: var(--ink); color: #fff; box-shadow: 0 10px 30px -10px rgba(0,0,0,.4); }
    .toast-success { background: #13603b; } .toast-error { background: #a3262b; }
    .toast button { background: none; border: 0; color: inherit; font-size: 1rem; cursor: pointer; }
    .backdrop { position: fixed; inset: 0; background: rgba(31,42,68,.45); display: grid; place-items: center; z-index: 999; padding: 1rem; }
    .dialog { background: #fff; border-radius: var(--r-md); padding: 1.5rem; max-width: 420px; width: 100%; }
    .actions { display: flex; gap: .75rem; justify-content: flex-end; margin-top: 1rem; }
  `,
})
export class FeedbackHostComponent {
  readonly toast = inject(ToastService);
  readonly confirm = inject(ConfirmService);
}
