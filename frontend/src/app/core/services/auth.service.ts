import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, finalize, of, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Message, Role, TokenResponse, User } from '../models/api.models';

const TOKEN_KEY = 've_token';
const USER_KEY = 've_user';

/** Sesión del usuario. El token se guarda en sessionStorage (se borra al cerrar el navegador). */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly api = `${environment.apiUrl}/auth`;

  private readonly _user = signal<User | null>(this.readUser());
  readonly user = this._user.asReadonly();
  readonly isLoggedIn = computed(() => this._user() !== null && this.token !== null);
  readonly role = computed<Role | null>(() => this._user()?.role ?? null);

  get token(): string | null {
    const token = this.storage()?.getItem(TOKEN_KEY) ?? null;
    const expires = this.storage()?.getItem(`${TOKEN_KEY}_exp`);
    if (token && expires && new Date(expires).getTime() < Date.now()) {
      this.clear();
      return null;
    }
    return token;
  }

  login(username: string, password: string): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.api}/login`, { username, password }).pipe(
      tap((res) => {
        this.storage()?.setItem(TOKEN_KEY, res.access_token);
        this.storage()?.setItem(`${TOKEN_KEY}_exp`, res.expires_at);
        this.setUser(res.user);
      }),
    );
  }

  register(data: {
    full_name: string; email: string; username: string; password: string; role: 'teacher' | 'guardian'; accept_terms: boolean;
  }): Observable<User> {
    return this.http.post<User>(`${this.api}/register`, data);
  }

  /** Revoca el token en el servidor y limpia la sesión local aunque el servidor falle. */
  logout(): void {
    const done = () => { this.clear(); this.router.navigateByUrl('/ingresar'); };
    if (!this.token) { done(); return; }
    this.http.post<Message>(`${this.api}/logout`, {}).pipe(catchError(() => of(null)), finalize(done)).subscribe();
  }

  refreshMe(): Observable<User> {
    return this.http.get<User>(`${this.api}/me`).pipe(tap((u) => this.setUser(u)));
  }

  updateProfile(data: { full_name?: string; email?: string }): Observable<User> {
    return this.http.patch<User>(`${this.api}/me`, data).pipe(tap((u) => this.setUser(u)));
  }

  changePassword(current_password: string, new_password: string): Observable<Message> {
    return this.http.post<Message>(`${this.api}/change-password`, { current_password, new_password });
  }

  requestPasswordReset(email: string): Observable<Message> {
    return this.http.post<Message>(`${this.api}/password-reset/request`, { email });
  }

  confirmPasswordReset(token: string, new_password: string): Observable<Message> {
    return this.http.post<Message>(`${this.api}/password-reset/confirm`, { token, new_password });
  }

  homeFor(role: Role | null): string {
    switch (role) {
      case 'student': return '/estudiante';
      case 'admin': return '/admin';
      case 'teacher':
      case 'guardian': return '/panel';
      default: return '/ingresar';
    }
  }

  /** Se llama ante un 401: la sesión expiró o fue revocada. */
  handleUnauthorized(): void {
    this.clear();
    this.router.navigate(['/ingresar'], { queryParams: { expirada: 1 } });
  }

  private setUser(user: User): void {
    this.storage()?.setItem(USER_KEY, JSON.stringify(user));
    this._user.set(user);
  }

  private clear(): void {
    this.storage()?.removeItem(TOKEN_KEY);
    this.storage()?.removeItem(`${TOKEN_KEY}_exp`);
    this.storage()?.removeItem(USER_KEY);
    this._user.set(null);
  }

  private readUser(): User | null {
    try {
      const raw = this.storage()?.getItem(USER_KEY);
      return raw ? (JSON.parse(raw) as User) : null;
    } catch {
      return null;
    }
  }

  private storage(): Storage | null {
    try { return window.sessionStorage; } catch { return null; }
  }
}
