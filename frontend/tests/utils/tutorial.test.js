import {
  TUTORIAL_SEEN_KEY,
  hasSeenTutorial,
  markTutorialSeen,
} from "../../src/utils/tutorial";

describe("tutorial seen flag", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => jest.restoreAllMocks());

  test("starts unseen, becomes seen after marking", () => {
    expect(hasSeenTutorial()).toBe(false);
    markTutorialSeen();
    expect(hasSeenTutorial()).toBe(true);
    expect(localStorage.getItem(TUTORIAL_SEEN_KEY)).toBe("1");
  });

  test("treats unavailable storage as seen and never throws", () => {
    jest.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    jest.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });

    expect(hasSeenTutorial()).toBe(true);
    expect(() => markTutorialSeen()).not.toThrow();
  });
});
