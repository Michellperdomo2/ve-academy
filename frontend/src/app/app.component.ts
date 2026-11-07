import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { FeedbackHostComponent } from './shared/components/feedback-host.component';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, FeedbackHostComponent],
  template: `<router-outlet /><ve-feedback-host />`,
})
export class AppComponent {}
