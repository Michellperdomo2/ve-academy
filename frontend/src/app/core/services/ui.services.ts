import { Injectable, signal } from '@angular/core';

export interface Toast { id: number; text: string; kind: 'success' | 'error' | 'info' }

/** Avisos no bloqueantes (reemplazan alert()). */
@Injectable({ providedIn: 'root' })
export class ToastService {
  private seq = 0;
  readonly toasts = signal<Toast[]>([]);

  show(text: string, kind: Toast['kind'] = 'info', ms = 4000): void {
    const toast = { id: ++this.seq, text, kind };
    this.toasts.update((t) => [...t, toast]);
    setTimeout(() => this.dismiss(toast.id), ms);
  }
  success(text: string): void { this.show(text, 'success'); }
  error(text: string): void { this.show(text, 'error', 6000); }
  dismiss(id: number): void { this.toasts.update((t) => t.filter((x) => x.id !== id)); }
}

/**
 * Lectura en voz alta con la Web Speech API del navegador (instrucciones de voz o audio,
 * marco conceptual 2.5 del documento). No usa servicios propios ni IA.
 */
@Injectable({ providedIn: 'root' })
export class SpeechService {
  readonly speaking = signal(false);
  readonly supported = typeof window !== 'undefined' && 'speechSynthesis' in window;

  speak(text: string, rate = 0.85): void {
    if (!this.supported || !text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'es-CO';
    utterance.rate = rate;
    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find((v) => v.lang === 'es-CO') ?? voices.find((v) => v.lang.startsWith('es'));
    if (voice) utterance.voice = voice;
    utterance.onstart = () => this.speaking.set(true);
    utterance.onend = utterance.onerror = () => this.speaking.set(false);
    window.speechSynthesis.speak(utterance);
  }

  stop(): void {
    if (this.supported) window.speechSynthesis.cancel();
    this.speaking.set(false);
  }
}

/** Diálogo de confirmación propio (no usa confirm() del navegador). */
@Injectable({ providedIn: 'root' })
export class ConfirmService {
  readonly request = signal<{ title: string; text: string; confirmLabel: string; resolve: (ok: boolean) => void } | null>(null);

  ask(title: string, text: string, confirmLabel = 'Confirmar'): Promise<boolean> {
    return new Promise((resolve) => this.request.set({ title, text, confirmLabel, resolve }));
  }
  close(ok: boolean): void {
    this.request()?.resolve(ok);
    this.request.set(null);
  }
}
