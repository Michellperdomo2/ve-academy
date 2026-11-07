import { Routes } from '@angular/router';

import { authGuard, guestGuard, roleGuard } from './core/guards/guards';

/** Rutas con carga diferida por módulo funcional (auth, estudiante, panel adulto, administración). */
export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'ingresar' },
  {
    path: '',
    canActivate: [guestGuard],
    loadChildren: () => import('./features/auth/auth.routes').then((m) => m.AUTH_ROUTES),
  },
  {
    path: 'restablecer',
    loadComponent: () => import('./features/auth/reset-password.component').then((m) => m.ResetPasswordComponent),
  },
  {
    path: 'estudiante',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['student'] },
    loadChildren: () => import('./features/student/student.routes').then((m) => m.STUDENT_ROUTES),
  },
  {
    path: 'panel',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['teacher', 'guardian'] },
    loadChildren: () => import('./features/adult/adult.routes').then((m) => m.ADULT_ROUTES),
  },
  {
    path: 'admin',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['admin'] },
    loadChildren: () => import('./features/admin/admin.routes').then((m) => m.ADMIN_ROUTES),
  },
  {
    path: '**',
    loadComponent: () => import('./shared/components/not-found.component').then((m) => m.NotFoundComponent),
  },
];
