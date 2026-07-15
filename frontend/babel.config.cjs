module.exports = {
  presets: [
    ["@babel/preset-env", { targets: { node: "current" } }],
    ["@babel/preset-react", { runtime: "automatic" }],
  ],
  env: {
    // Jest only (NODE_ENV=test): rewrite import.meta.env.* to process.env.*
    // so service modules parse under babel-jest. Vite builds are untouched.
    test: {
      plugins: ["babel-plugin-transform-vite-meta-env"],
    },
  },
};
