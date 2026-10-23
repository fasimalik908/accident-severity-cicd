/**
 * Single source of truth for the model inputs.
 *
 * The form is built from backend/feature_schema.json, the same file the
 * Flask API uses to validate requests. Nothing here is copied by hand:
 * if the backend schema changes, the form follows on the next build.
 */
import schemaJson from '../../../backend/feature_schema.json';
import samplePayloadJson from '../../../backend/test_payload.json';

export type FeatureKind = 'category' | 'number' | 'boolean';

export interface FeatureSpec {
  name: string;
  label: string;
  kind: FeatureKind;
  options?: string[];
  min?: number;
  max?: number;
  integer?: boolean;
}

export interface FeatureSchema {
  model_version: string;
  task: string;
  target: string;
  classes: number[];
  disclaimer: string;
  features: FeatureSpec[];
  test_metrics: Record<string, number>;
}

export type FeatureValue = string | number | boolean;
export type PredictionPayload = Record<string, FeatureValue>;

const schema = schemaJson as FeatureSchema;

export const FEATURES: readonly FeatureSpec[] = schema.features;
export const CLASSES: readonly number[] = schema.classes;
export const DISCLAIMER: string = schema.disclaimer;
export const MODEL_VERSION: string = schema.model_version;
export const TARGET: string = schema.target;

/** Valid example record (backend/test_payload.json) used by "Fill sample values". */
export const SAMPLE_INPUT: PredictionPayload = samplePayloadJson as PredictionPayload;
