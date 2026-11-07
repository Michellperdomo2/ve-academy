import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/** Lumi: búha mascota original de V&E Academy (SVG propio). */
@Component({
  selector: 've-mascot',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <svg [attr.width]="size()" [attr.height]="size()" viewBox="0 0 120 120" role="img" aria-label="Lumi, la búha lectora">
      <ellipse cx="60" cy="112" rx="34" ry="5" fill="#1f2a44" opacity=".08" />
      <path d="M22 70c0-30 17-52 38-52s38 22 38 52-17 40-38 40-38-10-38-40z" fill="#6c4fd1" />
      <path d="M36 82c0-14 11-22 24-22s24 8 24 22-11 24-24 24-24-10-24-24z" fill="#ece7fb" />
      <path d="M30 26l10 14M90 26L80 40" stroke="#6c4fd1" stroke-width="8" stroke-linecap="round" />
      <circle cx="44" cy="50" r="15" fill="#fff" /><circle cx="76" cy="50" r="15" fill="#fff" />
      <g [class.blink]="animate()">
        <circle cx="46" cy="51" r="6.5" fill="#1f2a44" /><circle cx="74" cy="51" r="6.5" fill="#1f2a44" />
        <circle cx="48" cy="49" r="2" fill="#fff" /><circle cx="76" cy="49" r="2" fill="#fff" />
      </g>
      <path d="M55 62l5 7 5-7z" fill="#ffc93c" />
      @switch (mood()) {
        @case ('happy') { <path d="M48 76q12 10 24 0" stroke="#1f2a44" stroke-width="3" fill="none" stroke-linecap="round" /> }
        @case ('think') { <circle cx="60" cy="78" r="3" fill="#1f2a44" /> }
      }
      <rect x="40" y="88" width="40" height="16" rx="3" fill="#ffc93c" />
      <path d="M60 88v16" stroke="#e0a400" stroke-width="2" />
      <path d="M44 93h12M44 98h10M64 93h12M64 98h10" stroke="#fff" stroke-width="1.6" stroke-linecap="round" />
    </svg>
  `,
  styles: `
    :host { display: inline-block; line-height: 0; }
    .blink { animation: blink 5s infinite; transform-origin: center 51px; transform-box: view-box; }
    @keyframes blink { 0%, 95%, 100% { transform: scaleY(1); } 97% { transform: scaleY(0.1); } }
  `,
})
export class MascotComponent {
  readonly size = input(96);
  readonly mood = input<'happy' | 'think' | 'calm'>('happy');
  readonly animate = input(true);
}
