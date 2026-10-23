import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { PredictionPayload } from './feature-schema';

/** Response body of POST /predict (see backend/app.py). */
export interface PredictionResponse {
  prediction: number;
  label: string;
  classes: number[];
  probabilities: number[];
  task: string;
  model_version: string;
  disclaimer: string;
}

/** Relative URL: the dev server proxies /api/* to the local Flask API (proxy.conf.json). */
export const PREDICT_URL = '/api/predict';

@Injectable({ providedIn: 'root' })
export class PredictionService {
  private readonly http = inject(HttpClient);

  predict(payload: PredictionPayload): Observable<PredictionResponse> {
    return this.http.post<PredictionResponse>(PREDICT_URL, payload);
  }
}
