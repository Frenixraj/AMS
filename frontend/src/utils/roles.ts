import type { User } from "@/types/auth";

export type AppRole = NonNullable<User["role"]>;

export function hasRole(user: User | null | undefined, roles: AppRole[]): boolean {
  if (!user?.role) return false;
  return roles.includes(user.role);
}

export function isAdminOrIT(user: User | null | undefined): boolean {
  return hasRole(user, ["ADMIN", "IT_TEAM"]);
}

export function isManagerOrAbove(user: User | null | undefined): boolean {
  return hasRole(user, ["ADMIN", "IT_TEAM", "MANAGER"]);
}
