import { describe, expect, it } from "vitest";
import { can, isRole } from "../roles";
import { dbErrorMessage, GENERIC_ERROR } from "../db-errors";

describe("roles", () => {
  it("recognises valid roles only", () => {
    expect(isRole("manager")).toBe(true);
    expect(isRole("superuser")).toBe(false);
    expect(isRole(undefined)).toBe(false);
  });

  it("only admins manage users and the company", () => {
    expect(can("admin", "manageUsers")).toBe(true);
    expect(can("manager", "manageUsers")).toBe(false);
    expect(can("driver", "manageOrganization")).toBe(false);
  });

  it("admins and managers manage vehicles, drivers do not", () => {
    expect(can("admin", "manageVehicles")).toBe(true);
    expect(can("manager", "manageVehicles")).toBe(true);
    expect(can("driver", "manageVehicles")).toBe(false);
  });
});

describe("dbErrorMessage", () => {
  it("translates known database errors", () => {
    expect(dbErrorMessage({ message: "last_admin" })).toMatch(/administrátora/);
  });
  it("hides unknown errors behind a generic message", () => {
    expect(dbErrorMessage({ message: "relation does not exist" })).toBe(GENERIC_ERROR);
    expect(dbErrorMessage(null)).toBe(GENERIC_ERROR);
  });
});
