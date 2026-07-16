import { render, screen, act } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import SignIn from "../src/pages/SignIn";

jest.mock("../src/hooks/useAuth", () => ({
  useAuth: jest.fn(),
}));

const { useAuth } = require("../src/hooks/useAuth");

function renderSignIn() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<SignIn />} />
        <Route path="/dashboard" element={<div>DASHBOARD PROBE</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function getGsiScript() {
  return document.querySelector('script[src*="gsi/client"]');
}

function stubGoogle() {
  const google = {
    accounts: {
      id: {
        initialize: jest.fn(),
        renderButton: jest.fn(),
      },
    },
  };
  window.google = google;
  return google.accounts.id;
}

describe("SignIn page", () => {
  afterEach(() => {
    delete window.google;
    jest.clearAllMocks();
  });

  test("shows the wordmark with the beta label", () => {
    useAuth.mockReturnValue({ user: null, login: jest.fn() });
    renderSignIn();
    expect(screen.getByText("Ask Clara")).toBeInTheDocument();
    expect(screen.getByText("(Beta Version)")).toBeInTheDocument();
  });

  test("redirects straight to the dashboard when already signed in", () => {
    useAuth.mockReturnValue({ user: { id: "u1" }, login: jest.fn() });
    renderSignIn();
    expect(screen.getByText("DASHBOARD PROBE")).toBeInTheDocument();
    expect(getGsiScript()).toBeNull();
  });

  test("loads the Google script and initializes GSI with the client id", () => {
    useAuth.mockReturnValue({ user: null, login: jest.fn() });
    renderSignIn();

    const script = getGsiScript();
    expect(script).not.toBeNull();

    const gsi = stubGoogle();
    act(() => script.onload());

    expect(gsi.initialize).toHaveBeenCalledWith(
      expect.objectContaining({ client_id: "test-client-id" }),
    );
    expect(gsi.renderButton).toHaveBeenCalledWith(
      expect.any(HTMLElement),
      expect.objectContaining({ theme: "outline" }),
    );
  });

  test("a successful Google credential signs in and navigates to the dashboard", async () => {
    const login = jest.fn().mockResolvedValue({ id: "u1" });
    useAuth.mockReturnValue({ user: null, login });
    renderSignIn();

    const gsi = stubGoogle();
    act(() => getGsiScript().onload());
    const { callback } = gsi.initialize.mock.calls[0][0];

    await act(async () => {
      await callback({ credential: "google-cred" });
    });

    expect(login).toHaveBeenCalledWith("google-cred");
    expect(screen.getByText("DASHBOARD PROBE")).toBeInTheDocument();
  });

  test("a failed sign-in shows the Temple-email alert and stays on the page", async () => {
    const login = jest.fn().mockRejectedValue(new Error("403"));
    useAuth.mockReturnValue({ user: null, login });
    const alertSpy = jest.spyOn(window, "alert").mockImplementation(() => {});
    renderSignIn();

    const gsi = stubGoogle();
    act(() => getGsiScript().onload());
    const { callback } = gsi.initialize.mock.calls[0][0];

    await act(async () => {
      await callback({ credential: "bad-cred" });
    });

    expect(alertSpy).toHaveBeenCalledWith(
      expect.stringContaining("Temple University email"),
    );
    expect(screen.queryByText("DASHBOARD PROBE")).not.toBeInTheDocument();
    alertSpy.mockRestore();
  });

  test("unmount removes the injected Google script", () => {
    useAuth.mockReturnValue({ user: null, login: jest.fn() });
    const { unmount } = renderSignIn();
    expect(getGsiScript()).not.toBeNull();

    unmount();
    expect(getGsiScript()).toBeNull();
  });
});
