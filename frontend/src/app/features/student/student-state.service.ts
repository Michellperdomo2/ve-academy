import { Injectable, inject, signal } from '@angular/core';

import { Student } from '../../core/models/api.models';
import { LearningService } from '../../core/services/api.services';

/** Estado compartido del estudiante (puntos y avatar visibles en la barra superior). */
@Injectable({ providedIn: 'root' })
export class StudentStateService {
  private readonly learning = inject(LearningService);
  readonly profile = signal<Student | null>(null);

  refresh(): void {
    this.learning.profile().subscribe((p) => this.profile.set(p));
  }
}
