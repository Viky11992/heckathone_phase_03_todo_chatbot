import { TaskResponse, TaskCreate, TaskUpdate, TaskToggleComplete } from './types';
import { authService } from './auth-service';

// Base API URL from environment or default
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

// API client class to handle all API requests
class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  // Helper method to get auth headers with JWT token
  private getAuthHeaders(): HeadersInit {
    const token = authService.getAuthToken();
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  // Get JWT token from auth system
  private async getJwtToken(): Promise<string | null> {
    // Use the auth service to get the token
    return authService.getAuthToken();
  }

  // Convert date string to datetime format for API
  private formatDateToDateTime(dateString: string | null | undefined): string | null {
    if (!dateString) {
      return null;
    }

    // If dateString is already in ISO datetime format, return as is
    if (dateString.includes('T')) {
      return dateString;
    }

    // Convert date string (YYYY-MM-DD) to datetime (YYYY-MM-DDT00:00:00)
    return `${dateString}T00:00:00`;
  }

  // Include token in request
  private async makeRequest(endpoint: string, options: RequestInit = {}) {
    let token = await this.getJwtToken();

    // If no token exists, try to get the user ID from localStorage and create a token
    if (!token) {
      const userId = authService.getUserId();
      const userEmail = localStorage.getItem('user_email');

      if (userId && userEmail) {
        // Generate a new token using the backend service
        try {
          const tokenResponse = await authService.generateToken({
            user_id: userId,
            email: userEmail,
            name: userEmail.split('@')[0]
          });

          if (tokenResponse.success && tokenResponse.token) {
            token = tokenResponse.token;
            // Always use the user_id returned by the backend to ensure consistency
            const returnedUserId = tokenResponse.user_id || userId;
            authService.setAuthData(token as string, returnedUserId, userEmail || '');
          }
        } catch (error) {
          console.error('Failed to generate token:', error);
          throw new Error('Authentication required. Please sign in.');
        }
      } else if (userEmail) {
        // If we have email but no user ID, create consistent user ID from email
        const newUserId = `user-${btoa(userEmail).replace(/[^a-zA-Z0-9]/g, '')}`;
        try {
          const tokenResponse = await authService.generateToken({
            user_id: newUserId,
            email: userEmail,
            name: userEmail.split('@')[0]
          });

          if (tokenResponse.success && tokenResponse.token) {
            token = tokenResponse.token;
            // Always use the user_id returned by the backend to ensure consistency
            const returnedUserId = tokenResponse.user_id || newUserId;
            authService.setAuthData(token as string, returnedUserId, userEmail || '');
          }
        } catch (error) {
          console.error('Failed to generate token:', error);
          throw new Error('Authentication required. Please sign in.');
        }
      } else {
        // If no user info exists, we can't proceed without authentication
        throw new Error('Authentication required. Please sign in.');
      }
    }

    const headers = {
      ...this.getAuthHeaders(),
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers
    };

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    // If we get a 401/403, try to refresh the token and retry the request
    if (response.status === 403 || response.status === 401) {
      try {
        const errorData = await response.json().catch(() => ({}));
        console.error('Auth error:', errorData);

        // Try to validate current token
        const currentToken = authService.getAuthToken();
        if (currentToken) {
          const validation = await authService.validateToken(currentToken);
          if (!validation.success) {
            // Token is invalid, clear it and try to generate a new one
            const userEmail = localStorage.getItem('user_email');
            authService.clearAuthData();

            // Generate a new token with the current user ID or derive from email if available
            let userId = authService.getUserId();

            // If no stored user ID but we have email, create one consistently
            if (!userId && userEmail) {
              userId = `user-${btoa(userEmail).replace(/[^a-zA-Z0-9]/g, '')}`;
            }
            // If still no user ID, create a generic one (though this shouldn't happen in normal flow)
            else if (!userId) {
              userId = `user-${Date.now()}`;
            }

            const tokenResponse = await authService.generateToken({
              user_id: userId,
              email: userEmail || `${userId}@example.com`,
              name: userEmail ? userEmail.split('@')[0] : `User ${userId}`
            });

            if (tokenResponse.success && tokenResponse.token) {
              // Use the user_id returned by the backend to ensure consistency
              const returnedUserId = tokenResponse.user_id || userId;
              authService.setAuthData(tokenResponse.token as string, returnedUserId, userEmail || `${returnedUserId}@example.com`);

              // Retry the request with the new token
              const retryHeaders = {
                ...this.getAuthHeaders(),
                'Authorization': `Bearer ${tokenResponse.token}`,
                ...options.headers
              };

              const retryResponse = await fetch(`${this.baseUrl}${endpoint}`, {
                ...options,
                headers: retryHeaders,
              });

              if (!retryResponse.ok) {
                const retryErrorData = await retryResponse.json().catch(() => ({}));

                // Handle validation errors (422) with more specific information
                if (retryResponse.status === 422 && retryErrorData.detail) {
                  // Format validation errors for better readability
                  let validationErrors = '';
                  if (Array.isArray(retryErrorData.detail)) {
                    validationErrors = retryErrorData.detail.map((err: any) =>
                      `${err.loc?.join('.')}: ${err.msg} (${err.type})`
                    ).join('; ');
                  }

                  throw new Error(`Validation Error: ${validationErrors || 'Invalid input data'} (Status: ${retryResponse.status})`);
                }

                throw new Error(retryErrorData.error?.message || `API request failed: ${retryResponse.status}`);
              }

              return retryResponse.json();
            }
          }
        }
      } catch (retryError) {
        console.error('Retry failed:', retryError);
      }

      // If retry failed, throw the original error
      const errorData = await response.json().catch(() => ({}));

      // Handle validation errors (422) with more specific information
      if ((response.status as number) === 422 && errorData.detail) {
        // Format validation errors for better readability
        let validationErrors = '';
        if (Array.isArray(errorData.detail)) {
          validationErrors = errorData.detail.map((err: any) =>
            `${err.loc?.join('.')}: ${err.msg} (${err.type})`
          ).join('; ');
        }

        throw new Error(`Validation Error: ${validationErrors || 'Invalid input data'} (Status: ${response.status})`);
      }

      throw new Error(errorData.error?.message || `API request failed: ${response.status}`);
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      // Handle validation errors (422) with more specific information
      if (response.status === 422 && errorData.detail) {
        // Format validation errors for better readability
        let validationErrors = '';
        if (Array.isArray(errorData.detail)) {
          validationErrors = errorData.detail.map((err: any) =>
            `${err.loc?.join('.')}: ${err.msg} (${err.type})`
          ).join('; ');
        }

        throw new Error(`Validation Error: ${validationErrors || 'Invalid input data'} (Status: ${response.status})`);
      }

      throw new Error(errorData.error?.message || `API request failed: ${response.status}`);
    }

    return response.json();
  }

  // Task-related API methods
  async getTasks(userId: string, params?: { status?: string; priority?: string; category?: string; sort?: string; page?: number; limit?: number }) {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status_filter', params.status);
    if (params?.priority) queryParams.append('priority_filter', params.priority);
    if (params?.category) queryParams.append('category_filter', params.category);
    if (params?.sort) queryParams.append('sort', params.sort);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const queryString = queryParams.toString();
    const endpoint = `/${userId}/tasks${queryString ? `?${queryString}` : ''}`;

    return this.makeRequest(endpoint, { method: 'GET' });
  }

  async createTask(userId: string, taskData: TaskCreate) {
    // Prepare task data by converting date string to datetime format if needed
    const preparedData = {
      ...taskData,
      due_date: this.formatDateToDateTime(taskData.due_date) || undefined
    };

    return this.makeRequest(`/${userId}/tasks`, {
      method: 'POST',
      body: JSON.stringify(preparedData),
    });
  }

  async getTask(userId: string, taskId: number) {
    return this.makeRequest(`/${userId}/tasks/${taskId}`, { method: 'GET' });
  }

  async updateTask(userId: string, taskId: number, taskData: TaskUpdate) {
    // Prepare task data by converting date string to datetime format if needed
    const preparedData = {
      ...taskData,
      due_date: this.formatDateToDateTime(taskData.due_date) || undefined
    };

    return this.makeRequest(`/${userId}/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(preparedData),
    });
  }

  async deleteTask(userId: string, taskId: number) {
    return this.makeRequest(`/${userId}/tasks/${taskId}`, { method: 'DELETE' });
  }

  async toggleTaskCompletion(userId: string, taskId: number, completionData: TaskToggleComplete) {
    return this.makeRequest(`/${userId}/tasks/${taskId}/complete`, {
      method: 'PATCH',
      body: JSON.stringify(completionData),
    });
  }

  async updateProfileImage(userId: string, image: string) {
    return this.makeRequest(`/${userId}/profile/image`, {
      method: 'PUT',
      body: JSON.stringify({ image }),
    });
  }

  // Chat-related API methods
  async sendChatMessage(messageData: { message: string; session_id?: string }) {
    return this.makeRequest('/chat', {
      method: 'POST',
      body: JSON.stringify(messageData),
    });
  }

  async getChatHistory(sessionId: string) {
    return this.makeRequest(`/chat/history/${sessionId}`, {
      method: 'GET',
    });
  }

  async getUserSessions() {
    return this.makeRequest('/chat/sessions', {
      method: 'GET',
    });
  }

  async clearChatHistory(sessionId: string) {
    return this.makeRequest(`/chat/clear/${sessionId}`, {
      method: 'DELETE',
    });
  }
}

// Export a singleton instance of the API client
export const api = new ApiClient();

// Export helper functions for easier usage
export const sendChatMessage = api.sendChatMessage.bind(api);
export const getChatHistory = api.getChatHistory.bind(api);
export const getUserSessions = api.getUserSessions.bind(api);
export const clearChatHistory = api.clearChatHistory.bind(api);

export default api;