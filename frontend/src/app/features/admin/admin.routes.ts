import { Routes } from '@angular/router';

import { AdultShellComponent } from '../adult/adult-shell.component';

export const ADMIN_ROUTES: Routes = [
  {
    path: '',
    component: AdultShellComponent,
    children: [
      { path: '', title: 'Administración · V&E Academy', loadComponent: () => import('./admin-overview.component').then((m) => m.AdminOverviewComponent) },
      { path: 'usuarios', title: 'Usuarios · V&E Academy', loadComponent: () => import('./users-admin.component').then((m) => m.UsersAdminComponent) },
      { path: 'estudiantes/:id', title: 'Reporte de progreso · V&E Academy', loadComponent: () => import('../adult/student-report.component').then((m) => m.StudentReportComponent) },
      { path: 'lecturas', title: 'Lecturas · V&E Academy', loadComponent: () => import('./readings-admin.component').then((m) => m.ReadingsAdminComponent) },
      { path: 'lecturas/nueva', title: 'Nueva lectura · V&E Academy', loadComponent: () => import('./reading-editor.component').then((m) => m.ReadingEditorComponent) },
      { path: 'lecturas/:id', title: 'Editar lectura · V&E Academy', loadComponent: () => import('./reading-editor.component').then((m) => m.ReadingEditorComponent) },
      { path: 'actividades', title: 'Actividades · V&E Academy', loadComponent: () => import('./activities-admin.component').then((m) => m.ActivitiesAdminComponent) },
      { path: 'actividades/nueva', title: 'Nueva actividad · V&E Academy', loadComponent: () => import('./activity-editor.component').then((m) => m.ActivityEditorComponent) },
      { path: 'actividades/:id', title: 'Editar actividad · V&E Academy', loadComponent: () => import('./activity-editor.component').then((m) => m.ActivityEditorComponent) },
      { path: 'categorias', title: 'Categorías · V&E Academy', loadComponent: () => import('./categories-admin.component').then((m) => m.CategoriesAdminComponent) },
      { path: 'gamificacion', title: 'Gamificación · V&E Academy', loadComponent: () => import('./gamification-admin.component').then((m) => m.GamificationAdminComponent) },
      { path: 'perfil', title: 'Mi perfil · V&E Academy', loadComponent: () => import('../adult/profile.component').then((m) => m.ProfileComponent) },
    ],
  },
];
