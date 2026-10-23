/** Hosts where the Flask API is expected to run next to the dev server. */
export const LOCAL_HOSTS: readonly string[] = ['localhost', '127.0.0.1'];

/**
 * True when the page is served from anywhere other than the local machine
 * (for example GitHub Pages). In that case only the static interface is
 * available and predictions are disabled.
 */
export function isStaticDeployment(hostname: string): boolean {
  return !LOCAL_HOSTS.includes(hostname);
}
