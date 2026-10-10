import { describe, expect, it } from "vitest";
import {
  isValidEmail,
  isValidName,
  isValidOtp,
  normalizeEmail,
  normalizeName,
  normalizeOtp,
  safeNextPath,
} from "../validation";

describe("email", () => {
  it("normalizes case and whitespace", () => {
    expect(normalizeEmail("  Jan.Novak@Firma.SK ")).toBe("jan.novak@firma.sk");
  });
  it("accepts ordinary addresses and rejects junk", () => {
    expect(isValidEmail("jan@firma.sk")).toBe(true);
    expect(isValidEmail("jan@firma")).toBe(false);
    expect(isValidEmail("jan firma@x.sk")).toBe(false);
    expect(isValidEmail("")).toBe(false);
  });
});

describe("name", () => {
  it("collapses whitespace", () => {
    expect(normalizeName("  Ján   Novák ")).toBe("Ján Novák");
  });
  it("requires 2–200 characters", () => {
    expect(isValidName("J")).toBe(false);
    expect(isValidName("Ján")).toBe(true);
    expect(isValidName("x".repeat(201))).toBe(false);
  });
});

describe("otp", () => {
  it("accepts six digits typed with spaces", () => {
    expect(isValidOtp(normalizeOtp("123 456"))).toBe(true);
    expect(isValidOtp("12345")).toBe(false);
    expect(isValidOtp("12345a")).toBe(false);
  });
});

describe("safeNextPath", () => {
  it("keeps local paths", () => {
    expect(safeNextPath("/users?x=1")).toBe("/users?x=1");
  });
  it.each([null, undefined, "", "https://evil.com", "//evil.com", "/\\evil.com", "users"])(
    "falls back for %s",
    (value) => {
      expect(safeNextPath(value)).toBe("/");
    },
  );
});
