import { Component, computed, inject, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import {
  AbstractControl,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { isStaticDeployment } from './deployment';
import {
  CLASSES,
  DISCLAIMER,
  FEATURES,
  FeatureSpec,
  FeatureValue,
  MODEL_VERSION,
  PredictionPayload,
  SAMPLE_INPUT,
} from './feature-schema';
import { PredictionResponse, PredictionService } from './prediction.service';

/** Rejects numbers with a fractional part. */
const integerValidator: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
  const value = control.value;
  if (value === null || value === undefined || value === '') {
    return null;
  }
  return Number.isInteger(Number(value)) ? null : { integer: true };
};

function validatorsFor(feature: FeatureSpec): ValidatorFn[] {
  const validators: ValidatorFn[] = [Validators.required];
  if (feature.kind === 'number') {
    if (feature.min !== undefined) validators.push(Validators.min(feature.min));
    if (feature.max !== undefined) validators.push(Validators.max(feature.max));
    if (feature.integer) validators.push(integerValidator);
  }
  return validators;
}

export interface ClassProbability {
  label: string;
  percent: number;
  predicted: boolean;
}

@Component({
  imports: [ReactiveFormsModule],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  private readonly predictionService = inject(PredictionService);

  protected readonly features = FEATURES;
  protected readonly classes = CLASSES;
  protected readonly disclaimer = DISCLAIMER;
  protected readonly schemaVersion = MODEL_VERSION;

  /** GitHub Pages (or any non-local host) serves only the static interface. */
  readonly deployedStatic = isStaticDeployment(window.location.hostname);

  readonly form = new FormGroup<Record<string, FormControl<FeatureValue | null>>>(
    Object.fromEntries(
      FEATURES.map((f) => [f.name, new FormControl<FeatureValue | null>(null, validatorsFor(f))]),
    ),
  );

  protected readonly submitted = signal(false);
  protected readonly loading = signal(false);
  protected readonly result = signal<PredictionResponse | null>(null);
  protected readonly apiError = signal<string | null>(null);

  protected readonly probabilityRows = computed<ClassProbability[]>(() => {
    const r = this.result();
    if (!r) return [];
    return r.classes.map((cls, i) => ({
      label: `Severity ${cls}`,
      percent: Math.round((r.probabilities[i] ?? 0) * 1000) / 10,
      predicted: cls === r.prediction,
    }));
  });

  protected inputId(feature: FeatureSpec): string {
    return 'f-' + feature.name.replace(/[^A-Za-z0-9_-]/g, '_');
  }

  protected showError(feature: FeatureSpec): boolean {
    const control = this.form.controls[feature.name];
    return control.invalid && (control.touched || this.submitted());
  }

  protected errorMessage(feature: FeatureSpec): string {
    const errors = this.form.controls[feature.name].errors;
    if (!errors) return '';
    if (errors['required']) {
      return feature.kind === 'number' ? 'Enter a number.' : 'Choose a value.';
    }
    if (errors['min'] || errors['max']) {
      return `Must be between ${feature.min} and ${feature.max}.`;
    }
    if (errors['integer']) {
      return 'Must be a whole number.';
    }
    return 'Invalid value.';
  }

  protected rangeHint(feature: FeatureSpec): string {
    if (feature.kind !== 'number') return '';
    const range = `${feature.min} to ${feature.max}`;
    return feature.integer ? `${range}, whole number` : range;
  }

  fillSample(): void {
    this.form.patchValue(SAMPLE_INPUT);
    this.form.markAllAsTouched();
    this.apiError.set(null);
  }

  resetForm(): void {
    this.form.reset();
    this.submitted.set(false);
    this.result.set(null);
    this.apiError.set(null);
  }

  /** Converts the form values into the JSON body expected by the API contract. */
  buildPayload(): PredictionPayload {
    const payload: PredictionPayload = {};
    for (const feature of FEATURES) {
      const value = this.form.controls[feature.name].value;
      if (feature.kind === 'number') {
        payload[feature.name] = Number(value);
      } else if (feature.kind === 'boolean') {
        payload[feature.name] = value === true || value === 'true';
      } else {
        payload[feature.name] = String(value);
      }
    }
    return payload;
  }

  submit(): void {
    this.submitted.set(true);
    this.form.markAllAsTouched();
    if (this.deployedStatic || this.form.invalid || this.loading()) {
      return;
    }
    this.loading.set(true);
    this.apiError.set(null);
    this.result.set(null);
    this.predictionService.predict(this.buildPayload()).subscribe({
      next: (response) => {
        this.result.set(response);
        this.loading.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.apiError.set(describeHttpError(err));
        this.loading.set(false);
      },
    });
  }
}

/** Turns an HTTP error (Flask 400 body, proxy failure, network error) into readable text. */
export function describeHttpError(err: HttpErrorResponse): string {
  if (err.status === 0) {
    return 'Could not reach the prediction API. Is the Flask server running on port 5000?';
  }
  const head = `HTTP ${err.status}${err.statusText ? ' ' + err.statusText : ''}`;
  const body = err.error;
  if (body && typeof body === 'object') {
    const parts: string[] = [];
    if (body.error) parts.push(String(body.error));
    if (body.field) parts.push(`field "${body.field}"`);
    if (body.detail) parts.push(String(body.detail));
    if (Array.isArray(body.missing) && body.missing.length) parts.push(`missing: ${body.missing.join(', ')}`);
    if (Array.isArray(body.extra) && body.extra.length) parts.push(`unexpected: ${body.extra.join(', ')}`);
    if (parts.length) return `${head}: ${parts.join(' - ')}`;
  }
  if (typeof body === 'string' && body.trim()) {
    return `${head}: ${body.trim().slice(0, 300)}`;
  }
  if (err.status >= 500) {
    return `${head}: the prediction API is unavailable. Start the Flask server and try again.`;
  }
  return head;
}
