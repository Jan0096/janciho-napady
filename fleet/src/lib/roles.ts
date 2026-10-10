export const ROLES = ["admin", "manager", "driver"] as const;
export type Role = (typeof ROLES)[number];

export const ROLE_LABELS: Record<Role, string> = {
  admin: "Administrátor",
  manager: "Správca",
  driver: "Vodič",
};

export const ROLE_DESCRIPTIONS: Record<Role, string> = {
  admin: "Nastavenia firmy, používatelia, všetko",
  manager: "Autá, doklady, schvaľovanie, kontroly, prehľady",
  driver: "Rezervácie, prevzatie auta, hlásenia",
};

export function isRole(value: unknown): value is Role {
  return typeof value === "string" && (ROLES as readonly string[]).includes(value);
}

/**
 * UI-level permissions. The database enforces the same rules (RLS + RPC checks);
 * this only decides what to show.
 */
const PERMISSIONS = {
  manageUsers: ["admin"],
  manageOrganization: ["admin"],
  manageVehicles: ["admin", "manager"],
} as const satisfies Record<string, readonly Role[]>;

export type Permission = keyof typeof PERMISSIONS;

export function can(role: Role, permission: Permission): boolean {
  return (PERMISSIONS[permission] as readonly Role[]).includes(role);
}
