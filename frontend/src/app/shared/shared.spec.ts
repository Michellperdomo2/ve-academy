import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SkillProgress } from '../core/models/api.models';
import { avatarIcon } from '../core/models/labels';
import { ConfirmService } from '../core/services/ui.services';
import { FeedbackHostComponent } from './components/feedback-host.component';
import { SkillBarsComponent } from './components/skill-bars.component';
import { WeeklyChartComponent } from './components/weekly-chart.component';

describe('Componentes compartidos', () => {
  it('SkillBars muestra el estado y la precisión de cada habilidad', () => {
    const fixture: ComponentFixture<SkillBarsComponent> = TestBed.createComponent(SkillBarsComponent);
    const skills: SkillProgress[] = [
      { skill: 'literal', label: '', answered: 5, correct_first_try: 5, accuracy: 100, status: 'strong' },
      { skill: 'critical', label: '', answered: 0, correct_first_try: 0, accuracy: null, status: 'not_started' },
    ];
    fixture.componentRef.setInput('skills', skills);
    fixture.detectChanges();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Comprensión literal');
    expect(text).toContain('Fortalecida');
    expect(text).toContain('100% de aciertos');
    expect(text).toContain('Aún no ha practicado');
  });

  it('WeeklyChart resume la semana para lectores de pantalla', () => {
    const fixture = TestBed.createComponent(WeeklyChartComponent);
    fixture.componentRef.setInput('days', [
      { date: '2026-11-01', readings: 2, activities: 1, points: 20 },
      { date: '2026-11-02', readings: 0, activities: 3, points: 30 },
    ]);
    fixture.detectChanges();
    const chart = (fixture.nativeElement as HTMLElement).querySelector('[role=img]');
    expect(chart?.getAttribute('aria-label')).toBe('Últimos 7 días: 2 lecturas y 4 actividades');
  });

  it('el diálogo de confirmación resuelve la promesa', async () => {
    const fixture = TestBed.createComponent(FeedbackHostComponent);
    const confirm = TestBed.inject(ConfirmService);
    const answer = confirm.ask('Eliminar', '¿Seguro?', 'Eliminar');
    fixture.detectChanges();
    const buttons = (fixture.nativeElement as HTMLElement).querySelectorAll<HTMLButtonElement>('.dialog button');
    buttons[1].click();
    expect(await answer).toBeTrue();
  });

  it('avatarIcon usa el búho por defecto', () => {
    expect(avatarIcon('cat')).toBe('🐱');
    expect(avatarIcon('desconocido')).toBe('🦉');
  });
});
