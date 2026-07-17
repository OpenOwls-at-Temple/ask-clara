export const TUTORIAL_SEEN_KEY = "clara.tutorialSeen";

export function hasSeenTutorial() {
  try {
    return window.localStorage.getItem(TUTORIAL_SEEN_KEY) === "1";
  } catch {
    // Storage unavailable — treat as seen so we never redirect-loop.
    return true;
  }
}

export function markTutorialSeen() {
  try {
    window.localStorage.setItem(TUTORIAL_SEEN_KEY, "1");
  } catch {
    // Ignore — worst case the tutorial auto-opens again next visit.
  }
}
