import { HttpErrorResponse, provideHttpClient, withInterceptors, HttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree, provideRouter } from '@angular/router';

import { authGuard, guestGuard, roleGuard } from './guards/guards';
import { authInterceptor, errorInterceptor, errorMessage } from './interceptors/interceptors';
import { TokenResponse } from './models/api.models';
import { AuthService } from './services/auth.service';
import { ToastService } from './services/ui.services';

const TOKEN: TokenResponse = {
  access_token: 'abc.def.ghi', token_type: 'bearer', expires_at: new Date(Date.now() + 3_600_000).toISOString(),
  user: { id: 1, username: 'sofia', email: null, full_name: 'Sofía', role: 'student', is_active: true,
    created_at: '', last_login_at: null, student_profile_id: 3 },
};

describe('Core: autenticación, guards e interceptores', () => {
  let http: HttpTestingController;
  let auth: AuthService;

  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([authInterceptor, errorInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpTestingController);
    auth = TestBed.inject(AuthService);
  });

  afterEach(() => http.verify());

  function doLogin(): void {
    auth.login('sofia', 'lectura1').subscribe();
    const req = http.expectOne('/api/v1/auth/login');
    expect(req.request.body).toEqual({ username: 'sofia', password: 'lectura1' });
    req.flush(TOKEN);
  }

  it('guarda la sesión al iniciar y calcula la ruta de inicio por rol', () => {
    expect(auth.isLoggedIn()).toBeFalse();
    doLogin();
    expect(auth.isLoggedIn()).toBeTrue();
    expect(auth.role()).toBe('student');
    expect(auth.homeFor('student')).toBe('/estudiante');
    expect(auth.homeFor('teacher')).toBe('/panel');
    expect(auth.homeFor('admin')).toBe('/admin');
  });

  it('el interceptor adjunta el token solo a la API', () => {
    doLogin();
    const client = TestBed.inject(HttpClient);
    client.get('/api/v1/me/profile').subscribe();
    expect(http.expectOne('/api/v1/me/profile').request.headers.get('Authorization')).toBe('Bearer abc.def.ghi');
    client.get('https://otro-sitio.example/data').subscribe();
    expect(http.expectOne('https://otro-sitio.example/data').request.headers.has('Authorization')).toBeFalse();
  });

  it('un 401 cierra la sesión y lleva al login', () => {
    doLogin();
    const router = TestBed.inject(Router);
    spyOn(router, 'navigate');
    TestBed.inject(HttpClient).get('/api/v1/me/profile').subscribe({ error: () => undefined });
    http.expectOne('/api/v1/me/profile').flush({ error: { code: 'unauthorized', message: 'x' } }, { status: 401, statusText: 'Unauthorized' });
    expect(auth.isLoggedIn()).toBeFalse();
    expect(router.navigate).toHaveBeenCalledWith(['/ingresar'], { queryParams: { expirada: 1 } });
  });

  it('un 403 muestra un aviso', () => {
    const toast = TestBed.inject(ToastService);
    TestBed.inject(HttpClient).get('/api/v1/users').subscribe({ error: () => undefined });
    http.expectOne('/api/v1/users').flush({ error: { code: 'forbidden', message: 'No tienes permiso.' } }, { status: 403, statusText: 'Forbidden' });
    expect(toast.toasts()[0].text).toBe('No tienes permiso.');
  });

  it('logout revoca el token en el servidor', () => {
    doLogin();
    auth.logout();
    http.expectOne('/api/v1/auth/logout').flush({ message: 'ok' });
    expect(auth.isLoggedIn()).toBeFalse();
  });

  it('errorMessage traduce errores de validación y de red', () => {
    const validation = new HttpErrorResponse({ status: 422, error: { error: { code: 'validation_error', message: 'Datos no válidos.',
      details: [{ field: 'username', message: 'Value error, muy corto' }] } } });
    expect(errorMessage(validation)).toBe('Datos no válidos. username: muy corto');
    expect(errorMessage(new HttpErrorResponse({ status: 0 }))).toContain('No hay conexión');
  });

  describe('guards', () => {
    const state = { url: '/estudiante' } as RouterStateSnapshot;
    const route = (roles: string[]) => ({ data: { roles } }) as unknown as ActivatedRouteSnapshot;
    const run = (fn: () => unknown) => TestBed.runInInjectionContext(fn);

    it('authGuard redirige al login sin sesión', () => {
      const result = run(() => authGuard(route([]), state)) as UrlTree;
      expect(result.toString()).toBe('/ingresar?volver=%2Festudiante');
    });

    it('roleGuard permite el rol correcto y redirige los demás', () => {
      doLogin();
      expect(run(() => roleGuard(route(['student']), state))).toBeTrue();
      expect((run(() => roleGuard(route(['admin']), state)) as UrlTree).toString()).toBe('/estudiante');
    });

    it('guestGuard envía al inicio a quien ya inició sesión', () => {
      expect(run(() => guestGuard(route([]), state))).toBeTrue();
      doLogin();
      expect((run(() => guestGuard(route([]), state)) as UrlTree).toString()).toBe('/estudiante');
    });
  });
});
