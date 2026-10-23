import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { App } from './app';
import { isStaticDeployment } from './deployment';
import { FEATURES, SAMPLE_INPUT } from './feature-schema';
import { PREDICT_URL } from './prediction.service';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should render the heading', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('US Accident Severity Prediction');
  });

  it('should render one input per schema feature (12)', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(FEATURES.length).toBe(12);
    expect(compiled.querySelectorAll('.field').length).toBe(12);
    expect(compiled.querySelectorAll('.field select, .field input').length).toBe(12);
  });

  it('should keep the form invalid until values are filled', () => {
    const fixture = TestBed.createComponent(App);
    expect(fixture.componentInstance.form.invalid).toBe(true);
    fixture.componentInstance.fillSample();
    expect(fixture.componentInstance.form.valid).toBe(true);
  });

  it('should reject out-of-range and non-integer numbers', () => {
    const app = TestBed.createComponent(App).componentInstance;
    app.fillSample();
    app.form.controls['Humidity(%)'].setValue(150);
    expect(app.form.controls['Humidity(%)'].hasError('max')).toBe(true);
    app.form.controls['Hour'].setValue(3.5);
    expect(app.form.controls['Hour'].hasError('integer')).toBe(true);
  });

  it('should build the payload exactly as the API contract expects', () => {
    const app = TestBed.createComponent(App).componentInstance;
    app.fillSample();
    expect(app.buildPayload()).toEqual(SAMPLE_INPUT);
  });

  it('should POST the payload to the proxied predict URL', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    const http = TestBed.inject(HttpTestingController);
    // The test DOM runs on http://localhost, so predictions are enabled here.
    expect(app.deployedStatic).toBe(false);
    app.fillSample();
    app.submit();
    const req = http.expectOne(PREDICT_URL);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(SAMPLE_INPUT);
    req.flush({
      prediction: 3,
      label: 'Severity 3',
      classes: [1, 2, 3, 4],
      probabilities: [0.1, 0.2, 0.6, 0.1],
      task: 'classification',
      model_version: '1.0',
      disclaimer: 'x',
    });
    http.verify();
  });
});

describe('isStaticDeployment', () => {
  it('treats localhost and 127.0.0.1 as local', () => {
    expect(isStaticDeployment('localhost')).toBe(false);
    expect(isStaticDeployment('127.0.0.1')).toBe(false);
  });

  it('treats any other host (e.g. GitHub Pages) as static', () => {
    expect(isStaticDeployment('someone.github.io')).toBe(true);
  });
});
