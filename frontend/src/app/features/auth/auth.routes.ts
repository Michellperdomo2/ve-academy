import { Routes } from '@angular/router';

import { AuthLayoutComponent } from './auth-layout.component';

export const AUTH_ROUTES: Routes = [
  {
    path: '',
    component: AuthLayoutComponent,
    children: [
      { path: 'ingresar', title: 'Ingresar · V&E Academy', loadComponent: () => import('./login.component').then((m) => m.LoginComponent) },
      { path: 'registro', title: 'Crear cuenta · V&E Academy', loadComponent: () => import('./register.component').then((m) => m.RegisterComponent) },
      { path: 'recuperar', title: 'Recuperar contraseña · V&E Academy', loadComponent: () => import('./forgot-password.component').then((m) => m.ForgotPasswordComponent) },
    ],
  },
];
