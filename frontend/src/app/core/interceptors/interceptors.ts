import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';

import { environment } from '../../../environments/environment';
import { ApiError } from '../models/api.models';
import { AuthService } from '../services/auth.service';
import { ToastService } from '../services/ui.services';

/** Adjunta el token JWT solo a las peticiones dirigidas a nuestra API. */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthService).token;
  if (token && req.url.startsWith(environment.apiUrl)) {
    req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  }
  return next(req);
};

/** Extrae el mensaje legible del formato de error del backend. */
export function errorMessage(err: unknown): string {
  if (err instanceof HttpErrorResponse) {
    const body = err.error as ApiError | null;
    if (body?.error) {
      const details = body.error.details;
      if (Array.isArray(details) && details.length && typeof details[0] === 'object' && details[0] && 'message' in details[0]) {
        return `${body.error.message} ${(details as { field: string; message: string }[])
          .map((d) => `${d.field}: ${d.message.replace(/^Value error, /, '')}`).join(' · ')}`;
      }
      return body.error.message;
    }
    if (err.status === 0) return 'No hay conexión con el servidor. Revisa tu internet e inténtalo de nuevo.';
  }
  return 'Ocurrió un error inesperado.';
}

/**
 * Manejo global: 401 cierra la sesión; 403, 429, 5xx y errores de red muestran un aviso.
 * Los 4xx de validación los maneja cada formulario con `errorMessage()`.
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const toast = inject(ToastService);
  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      const isLogin = req.url.endsWith('/auth/login');
      if (err.status === 401 && !isLogin) {
        auth.handleUnauthorized();
      } else if (err.status === 403 || err.status === 429 || err.status >= 500 || err.status === 0) {
        toast.error(errorMessage(err));
      }
      return throwError(() => err);
    }),
  );
};
