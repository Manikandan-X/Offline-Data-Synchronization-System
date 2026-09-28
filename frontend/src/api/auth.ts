import { apiClient } from "./client";
import type { TokenResponse, User } from "@/types";

export interface RegisterPayload {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ProfileUpdatePayload {
  first_name?: string;
  last_name?: string;
  email?: string;
}

export interface PasswordChangePayload {
  current_password: string;
  new_password: string;
}

export const authApi = {
  register: (data: RegisterPayload) =>
    apiClient.post<User>("/auth/register", data).then((r) => r.data),

  login: (data: LoginPayload) =>
    apiClient.post<TokenResponse>("/auth/login", data).then((r) => r.data),

  me: () => apiClient.get<User>("/auth/me").then((r) => r.data),

  updateProfile: (data: ProfileUpdatePayload) =>
    apiClient.put<User>("/auth/me", data).then((r) => r.data),

  changePassword: (data: PasswordChangePayload) =>
    apiClient.put<User>("/auth/me/password", data).then((r) => r.data),
};
