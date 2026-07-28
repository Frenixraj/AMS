import type { User } from "@/types/auth";

export type AppRole = NonNullable<User["role"]>;

export function hasRole(user: User | null | undefined, roles: AppRole[]): boolean {
  if (!user?.role) return false;
  return roles.includes(user.role);
}

/** Admin or Asset Manager (legacy IT_TEAM still treated as ops). */
export function isAdminOrAssetManager(user: User | null | undefined): boolean {
  return hasRole(user, ["ADMIN", "ASSET_MANAGER", "IT_TEAM"]);
}

/** @deprecated use isAdminOrAssetManager */
export function isAdminOrIT(user: User | null | undefined): boolean {
  return isAdminOrAssetManager(user);
}

export function isManagerOrAbove(user: User | null | undefined): boolean {
  return hasRole(user, ["ADMIN", "ASSET_MANAGER", "IT_TEAM", "MANAGER"]);
}

export function isAdmin(user: User | null | undefined): boolean {
  return hasRole(user, ["ADMIN"]);
}

export function isManager(user: User | null | undefined): boolean {
  return hasRole(user, ["MANAGER"]);
}

export function isEmployee(user: User | null | undefined): boolean {
  return hasRole(user, ["EMPLOYEE"]);
}
