import "@testing-library/jest-dom";
import { vi } from "vitest";

// jsdom does not implement matchMedia (used for system theme detection).
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// jsdom does not implement scrollIntoView.
Element.prototype.scrollIntoView = vi.fn();
