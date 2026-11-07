import { Routes } from '@angular/router';

import { roleGuard } from '../../core/guards/guards';
import { AdultShellComponent } from './adult-shell.component';

export const ADULT_ROUTES: Routes = [
  {
    path: '',
    component: AdultShellComponent,
    children: [
      { path: '', title: 'Panel · V&E Academy', loadComponent: () => import('./students-panel.component').then((m) => m.StudentsPanelComponent) },
      { path: 'estudiantes/:id', title: 'Reporte de progreso · V&E Academy', loadComponent: () => import('./student-report.component').then((m) => m.StudentReportComponent) },
      {
        path: 'aulas', title: 'Aulas · V&E Academy', canActivate: [roleGuard], data: { roles: ['teacher'] },
        loadComponent: () => import('./classrooms.component').then((m) => m.ClassroomsComponent),
      },
      {
        path: 'aulas/:id', title: 'Estadísticas del aula · V&E Academy', canActivate: [roleGuard], data: { roles: ['teacher'] },
        loadComponent: () => import('./classroom-stats.component').then((m) => m.ClassroomStatsComponent),
      },
      { path: 'perfil', title: 'Mi perfil · V&E Academy', loadComponent: () => import('./profile.component').then((m) => m.ProfileComponent) },
    ],
  },
];
