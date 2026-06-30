module.exports = {
  testEnvironment: "jest-environment-jsdom",
  transform: { "^.+\\.[jt]sx?$": "babel-jest" },
  moduleNameMapper: { "\\.(css|less|scss)$": "<rootDir>/src/__mocks__/styleMock.js" },
  setupFilesAfterEnv: ["<rootDir>/src/__mocks__/setupTests.js"],
  testMatch: ["<rootDir>/tests/**/*.test.{js,jsx}"],
};
