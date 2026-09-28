import { apiClient } from "./client";
import type { User, UserListResponse } from "@/types";

export interface UserSearchParams {
  page?: number;
  page_size?: number;
  search?: string;
  role_id?: number;
  is_active?: boolean;
}

export interface CreateUserPayload {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  role_id: number;
}

export interface UpdateUserPayload {
  first_name?: string;
  last_name?: string;
  email?: string;
}

export const usersApi = {
  list: (params: UserSearchParams) =>
    apiClient.get<UserListResponse>("/users", { params }).then((r) => r.data),

  get: (id: number) => apiClient.get<User>(`/users/${id}`).then((r) => r.data),

  create: (data: CreateUserPayload) =>
    apiClient.post<User>("/users", data).then((r) => r.data),

  update: (id: number, data: UpdateUserPayload) =>
    apiClient.put<User>(`/users/${id}`, data).then((r) => r.data),

  changeRole: (id: number, role_id: number) =>
    apiClient.patch<User>(`/users/${id}/role`, { role_id }).then((r) => r.data),

  activate: (id: number) => apiClient.patch<User>(`/users/${id}/activate`).then((r) => r.data),

  deactivate: (id: number) =>
    apiClient.patch<User>(`/users/${id}/deactivate`).then((r) => r.data),

  remove: (id: number) => apiClient.delete(`/users/${id}`),
};
