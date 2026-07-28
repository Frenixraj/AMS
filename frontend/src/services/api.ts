import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { tokenStorage } from "@/utils/tokenStorage";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function subscribeTokenRefresh(callback: (token: string) => void): void {
  refreshSubscribers.push(callback);
}

function onTokenRefreshed(token: string): void {
  refreshSubscribers.forEach((callback) => callback(token));
  refreshSubscribers = [];
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // Let the browser set multipart boundary for FormData uploads.
  if (typeof FormData !== "undefined" && config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    const refreshToken = tokenStorage.getRefreshToken();
    if (!refreshToken) {
      tokenStorage.clearTokens();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve) => {
        subscribeTokenRefresh((token: string) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          resolve(apiClient(originalRequest));
        });
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const response = await axios.post<{ access: string }>(
        `${API_BASE_URL}/auth/token/refresh/`,
        { refresh: refreshToken }
      );

      const newAccessToken = response.data.access;
      tokenStorage.setTokens(newAccessToken, refreshToken);
      onTokenRefreshed(newAccessToken);

      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      return apiClient(originalRequest);
    } catch (refreshError) {
      tokenStorage.clearTokens();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);
