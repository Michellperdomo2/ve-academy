import { Routes } from '@angular/router';

import { StudentShellComponent } from './student-shell.component';

export const STUDENT_ROUTES: Routes = [
  {
    path: '',
    component: StudentShellComponent,
    children: [
      { path: '', title: 'Inicio · V&E Academy', loadComponent: () => import('./student-home.component').then((m) => m.StudentHomeComponent) },
      { path: 'lecturas', title: 'Mi biblioteca · V&E Academy', loadComponent: () => import('./readings-list.component').then((m) => m.ReadingsListComponent) },
      { path: 'lecturas/:id', title: 'Leer · V&E Academy', loadComponent: () => import('./reading-view.component').then((m) => m.ReadingViewComponent) },
      { path: 'actividades', title: 'Juegos · V&E Academy', loadComponent: () => import('./activities-list.component').then((m) => m.ActivitiesListComponent) },
      { path: 'actividades/:id', title: 'Jugar · V&E Academy', loadComponent: () => import('./activity-player.component').then((m) => m.ActivityPlayerComponent) },
      { path: 'logros', title: 'Mis logros · V&E Academy', loadComponent: () => import('./achievements.component').then((m) => m.AchievementsComponent) },
    ],
  },
];
