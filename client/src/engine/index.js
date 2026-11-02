import { ENGINE } from '../../config';
import { LocalEngine } from './LocalEngine';
import { RemoteEngine } from './RemoteEngine';

const MODE_KEY = 'datalakeStudio.engine';

// The engine the whole app runs on. There is one per page: switching engines reloads the app.
let engine = null;

// Whether this build has a backend to choose (the public build only runs in the browser)
export const canChooseEngine = ENGINE === 'remote';

export function engineMode() {
  if (!canChooseEngine) return 'local';
  try {
    return localStorage.getItem(MODE_KEY) === 'local' ? 'local' : 'remote';
  } catch (_) {
    return 'remote';
  }
}

export function getEngine() {
  if (!engine) engine = engineMode() === 'local' ? new LocalEngine() : new RemoteEngine();
  return engine;
}

export function useEngine() {
  return getEngine();
}

export function switchEngine(mode) {
  try {
    localStorage.setItem(MODE_KEY, mode);
  } catch (_) { /* storage blocked: the mode can't be remembered */ }
  window.location.reload();
}

// Tests swap in a fake engine
export function setEngine(newEngine) {
  engine = newEngine;
}
