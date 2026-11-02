import { RemoteEngine } from './RemoteEngine';

// The engine the whole app runs on. There is one per page: switching engines reloads the app.
let engine = null;

export function getEngine() {
  if (!engine) engine = new RemoteEngine();
  return engine;
}

export function useEngine() {
  return getEngine();
}

// Tests swap in a fake engine
export function setEngine(newEngine) {
  engine = newEngine;
}
