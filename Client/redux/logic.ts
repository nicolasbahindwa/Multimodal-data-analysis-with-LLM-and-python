# Enterprise-Level User Authentication with Redux Toolkit and RTK Query

This guide demonstrates how to build a robust, type-safe user authentication system using Redux Toolkit and RTK Query, following enterprise best practices with strong separation of concerns. We'll cover:

- Environment configuration
- User CRUD operations
- Authentication and token management
- Performance monitoring middleware
- Enterprise-level logging
- State persistence
- Advanced folder structure for scalability

## Project Structure

```
src/
├── app/
│   ├── root-reducer.ts
│   ├── root-saga.ts
│   ├── store/
│   │   ├── index.ts
│   │   ├── configureStore.ts
│   │   ├── persistConfig.ts
│   │   └── middlewareConfig.ts
│   └── hooks/
│       ├── index.ts
│       ├── useAppDispatch.ts
│       ├── useAppSelector.ts
│       └── useAuth.ts
├── config/
│   ├── index.ts
│   ├── environment.ts
│   └── constants.ts
├── features/
│   ├── auth/
│   │   ├── api/
│   │   │   ├── index.ts
│   │   │   ├── authApi.ts
│   │   │   └── types.ts
│   │   ├── components/
│   │   │   ├── LoginForm.tsx
│   │   │   └── RegisterForm.tsx
│   │   ├── hooks/
│   │   │   ├── useLogin.ts
│   │   │   └── useLogout.ts
│   │   ├── store/
│   │   │   ├── index.ts
│   │   │   ├── authSlice.ts
│   │   │   ├── selectors.ts
│   │   │   └── actions.ts
│   │   ├── utils/
│   │   │   └── validators.ts
│   │   └── index.ts
│   └── users/
│       ├── api/
│       │   ├── index.ts
│       │   ├── usersApi.ts
│       │   └── types.ts
│       ├── components/
│       │   ├── UserProfile.tsx
│       │   └── UserList.tsx
│       ├── hooks/
│       │   ├── useUserProfile.ts
│       │   └── useUserManagement.ts
│       ├── store/
│       │   ├── index.ts
│       │   ├── usersSlice.ts
│       │   ├── selectors.ts
│       │   └── actions.ts
│       └── index.ts
├── middleware/
│   ├── index.ts
│   ├── performance/
│   │   ├── index.ts
│   │   ├── performanceMonitoring.ts
│   │   └── metrics.ts
│   ├── error/
│   │   ├── index.ts
│   │   └── errorHandler.ts
│   └── logger/
│       ├── index.ts
│       ├── logger.ts
│       └── formatters.ts
├── services/
│   ├── index.ts
│   ├── api/
│   │   ├── index.ts
│   │   ├── apiClient.ts
│   │   └── interceptors.ts
│   ├── storage/
│   │   ├── index.ts
│   │   ├── localStorage.ts
│   │   └── sessionStorage.ts
│   ├── token/
│   │   ├── index.ts
│   │   ├── tokenService.ts
│   │   └── tokenInterceptor.ts
│   └── analytics/
│       ├── index.ts
│       └── analyticsService.ts
├── types/
│   ├── index.ts
│   ├── api.ts
│   ├── auth.ts
│   ├── user.ts
│   └── common.ts
├── utils/
│   ├── index.ts
│   ├── validation.ts
│   ├── formatting.ts
│   └── errorHandling.ts
└── App.tsx
```

## 1. Environment Configuration

First, create a `.env` file at the project root:

```
# .env
REACT_APP_API_URL=https://api.example.com
REACT_APP_API_TIMEOUT=30000
REACT_APP_API_VERSION=v1
REACT_APP_ACCESS_TOKEN_EXPIRY=3600
REACT_APP_REFRESH_TOKEN_EXPIRY=604800
REACT_APP_LOG_LEVEL=info
REACT_APP_PERFORMANCE_MONITORING=true
REACT_APP_ERROR_TRACKING=true
REACT_APP_ANALYTICS_ENABLED=true
REACT_APP_FEATURE_FLAG_ADMIN_PANEL=true
REACT_APP_FEATURE_FLAG_ENHANCED_SECURITY=true
```

Let's create a more robust configuration system:

```typescript
// src/config/constants.ts
/**
 * Application-wide constants
 */
export const APP_NAME = 'Enterprise Auth App';
export const APP_VERSION = '1.0.0';

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    REFRESH: '/auth/refresh',
    LOGOUT: '/auth/logout',
    VERIFY: '/auth/verify',
  },
  USERS: {
    ME: '/users/me',
    PASSWORD: '/users/me/password',
    ALL: '/users',
    BY_ID: (id: string) => `/users/${id}`,
  },
};

export const LOCAL_STORAGE_KEYS = {
  ACCESS_TOKEN: 'auth_access_token',
  REFRESH_TOKEN: 'auth_refresh_token',
  EXPIRES_AT: 'auth_expires_at',
  USER: 'auth_user',
  THEME: 'app_theme',
  LANGUAGE: 'app_language',
};

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  INTERNAL_SERVER_ERROR: 500,
};

export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  SERVER_ERROR: 'Server error. Please try again later.',
  UNAUTHORIZED: 'Your session has expired. Please log in again.',
  VALIDATION_ERROR: 'Please check your input and try again.',
};

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';
```

```typescript
// src/config/environment.ts
import { LogLevel } from './constants';

export interface Environment {
  // API Configuration
  API_URL: string;
  API_TIMEOUT: number;
  API_VERSION: string;
  
  // Token Management
  ACCESS_TOKEN_EXPIRY: number;
  REFRESH_TOKEN_EXPIRY: number;
  
  // Monitoring & Logging
  LOG_LEVEL: LogLevel;
  PERFORMANCE_MONITORING: boolean;
  ERROR_TRACKING: boolean;
  
  // Analytics
  ANALYTICS_ENABLED: boolean;
  
  // Feature Flags
  FEATURE_FLAGS: {
    ADMIN_PANEL: boolean;
    ENHANCED_SECURITY: boolean;
  };
}

/**
 * Environment configuration singleton
 * Provides type-safe access to environment variables with
 * strong validation and default values
 */
class EnvironmentConfig {
  private static instance: EnvironmentConfig;
  private config: Environment;

  private constructor() {
    this.validateRequiredEnvVars();
    
    this.config = {
      // API Configuration
      API_URL: this.getEnvVar('REACT_APP_API_URL', 'http://localhost:3001'),
      API_TIMEOUT: this.getEnvVarAsNumber('REACT_APP_API_TIMEOUT', 30000),
      API_VERSION: this.getEnvVar('REACT_APP_API_VERSION', 'v1'),
      
      // Token Management
      ACCESS_TOKEN_EXPIRY: this.getEnvVarAsNumber('REACT_APP_ACCESS_TOKEN_EXPIRY', 3600),
      REFRESH_TOKEN_EXPIRY: this.getEnvVarAsNumber('REACT_APP_REFRESH_TOKEN_EXPIRY', 604800),
      
      // Monitoring & Logging
      LOG_LEVEL: this.getEnvVarAsLogLevel('REACT_APP_LOG_LEVEL', 'info'),
      PERFORMANCE_MONITORING: this.getEnvVarAsBoolean('REACT_APP_PERFORMANCE_MONITORING', false),
      ERROR_TRACKING: this.getEnvVarAsBoolean('REACT_APP_ERROR_TRACKING', false),
      
      // Analytics
      ANALYTICS_ENABLED: this.getEnvVarAsBoolean('REACT_APP_ANALYTICS_ENABLED', false),
      
      // Feature Flags
      FEATURE_FLAGS: {
        ADMIN_PANEL: this.getEnvVarAsBoolean('REACT_APP_FEATURE_FLAG_ADMIN_PANEL', false),
        ENHANCED_SECURITY: this.getEnvVarAsBoolean('REACT_APP_FEATURE_FLAG_ENHANCED_SECURITY', false),
      },
    };
  }

  /**
   * Ensures critical environment variables are present
   */
  private validateRequiredEnvVars(): void {
    const requiredVars = ['REACT_APP_API_URL'];
    
    for (const varName of requiredVars) {
      if (!process.env[varName]) {
        console.error(`Missing required environment variable: ${varName}`);
        throw new Error(`Missing required environment variable: ${varName}`);
      }
    }
  }

  /**
   * Gets an environment variable with a default fallback
   */
  private getEnvVar(key: string, defaultValue: string): string {
    return process.env[key] || defaultValue;
  }

  /**
   * Converts an environment variable to a number
   */
  private getEnvVarAsNumber(key: string, defaultValue: number): number {
    const value = process.env[key];
    if (!value) return defaultValue;
    
    const parsed = Number(value);
    return isNaN(parsed) ? defaultValue : parsed;
  }

  /**
   * Converts an environment variable to a boolean
   */
  private getEnvVarAsBoolean(key: string, defaultValue: boolean): boolean {
    const value = process.env[key];
    if (!value) return defaultValue;
    
    return value.toLowerCase() === 'true';
  }

  /**
   * Converts an environment variable to a log level with validation
   */
  private getEnvVarAsLogLevel(key: string, defaultValue: LogLevel): LogLevel {
    const value = process.env[key] as LogLevel;
    const validLevels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
    
    if (!value || !validLevels.includes(value)) {
      return defaultValue;
    }
    
    return value;
  }

  /**
   * Returns the singleton instance
   */
  public static getInstance(): EnvironmentConfig {
    if (!EnvironmentConfig.instance) {
      EnvironmentConfig.instance = new EnvironmentConfig();
    }
    return EnvironmentConfig.instance;
  }

  /**
   * Retrieves the environment configuration
   */
  public getConfig(): Environment {
    return this.config;
  }
}

// Export as a singleton
export const env = EnvironmentConfig.getInstance().getConfig();
```

```typescript
// src/config/index.ts
export * from './constants';
export * from './environment';
```

## 2. Type Definitions

Define core types for our application:

```typescript
// src/types/index.ts
export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  createdAt: string;
  updatedAt: string;
}

export type UserRole = 'admin' | 'user' | 'guest';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

export interface RefreshTokenRequest {
  refreshToken: string;
}

export interface UpdateUserRequest {
  firstName?: string;
  lastName?: string;
  email?: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

export interface ApiError {
  status: number;
  data: {
    message: string;
    errors?: Record<string, string[]>;
  };
}
```

## 3. Enhanced Service Architecture

Let's create a robust service architecture starting with storage services and token management:

```typescript
// src/services/storage/localStorage.ts
import { logger } from '../../middleware/logger';

/**
 * Enhanced localStorage service with error handling, encryption, and compression capabilities
 */
export class LocalStorageService {
  /**
   * Stores a value in localStorage with optional encryption
   */
  public static setItem<T>(key: string, value: T, encrypt: boolean = false): void {
    try {
      const stringValue = typeof value === 'string' ? value : JSON.stringify(value);
      const storedValue = encrypt ? this.encryptValue(stringValue) : stringValue;
      localStorage.setItem(key, storedValue);
    } catch (error) {
      logger.error('LocalStorageService: Failed to set item', { key, error });
      throw new Error(`Failed to store item: ${key}`);
    }
  }

  /**
   * Retrieves a value from localStorage with automatic decryption if needed
   */
  public static getItem<T>(key: string, isJson: boolean = true, encrypted: boolean = false): T | null {
    try {
      const value = localStorage.getItem(key);
      if (!value) return null;

      const decryptedValue = encrypted ? this.decryptValue(value) : value;
      return isJson ? JSON.parse(decryptedValue) as T : (decryptedValue as unknown as T);
    } catch (error) {
      logger.error('LocalStorageService: Failed to get item', { key, error });
      return null;
    }
  }

  /**
   * Removes an item from localStorage
   */
  public static removeItem(key: string): void {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      logger.error('LocalStorageService: Failed to remove item', { key, error });
    }
  }

  /**
   * Clears all items from localStorage
   */
  public static clear(): void {
    try {
      localStorage.clear();
    } catch (error) {
      logger.error('LocalStorageService: Failed to clear storage', { error });
    }
  }

  /**
   * Basic encryption implementation (in production, use a proper encryption library)
   */
  private static encryptValue(value: string): string {
    // In a real enterprise app, implement proper encryption (e.g., with CryptoJS)
    // This is just a placeholder to illustrate the concept
    return btoa(value);
  }

  /**
   * Basic decryption implementation
   */
  private static decryptValue(value: string): string {
    // In a real enterprise app, implement proper decryption
    return atob(value);
  }
}
```

```typescript
// src/services/storage/sessionStorage.ts
import { logger } from '../../middleware/logger';

/**
 * SessionStorage service with consistent API and error handling
 */
export class SessionStorageService {
  /**
   * Stores a value in sessionStorage
   */
  public static setItem<T>(key: string, value: T): void {
    try {
      const stringValue = typeof value === 'string' ? value : JSON.stringify(value);
      sessionStorage.setItem(key, stringValue);
    } catch (error) {
      logger.error('SessionStorageService: Failed to set item', { key, error });
      throw new Error(`Failed to store item in session: ${key}`);
    }
  }

  /**
   * Retrieves a value from sessionStorage
   */
  public static getItem<T>(key: string, isJson: boolean = true): T | null {
    try {
      const value = sessionStorage.getItem(key);
      if (!value) return null;
      
      return isJson ? JSON.parse(value) as T : (value as unknown as T);
    } catch (error) {
      logger.error('SessionStorageService: Failed to get item', { key, error });
      return null;
    }
  }

  /**
   * Removes an item from sessionStorage
   */
  public static removeItem(key: string): void {
    try {
      sessionStorage.removeItem(key);
    } catch (error) {
      logger.error('SessionStorageService: Failed to remove item', { key, error });
    }
  }

  /**
   * Clears all items from sessionStorage
   */
  public static clear(): void {
    try {
      sessionStorage.clear();
    } catch (error) {
      logger.error('SessionStorageService: Failed to clear session storage', { error });
    }
  }
}
```

```typescript
// src/services/storage/index.ts
export * from './localStorage';
export * from './sessionStorage';
```

```typescript
// src/services/token/tokenService.ts
import { env } from '../../config/environment';
import { LOCAL_STORAGE_KEYS } from '../../config/constants';
import { AuthResponse } from '../../types/auth';
import { LocalStorageService } from '../storage/localStorage';
import { logger } from '../../middleware/logger';
import { EventEmitter } from '../../utils/eventEmitter';

export interface TokenData {
  accessToken: string;
  refreshToken: string;
  accessTokenExpiresAt: number;
  refreshTokenExpiresAt: number;
}

export enum TokenEventType {
  TOKEN_STORED = 'token_stored',
  TOKEN_RETRIEVED = 'token_retrieved',
  TOKEN_REFRESHED = 'token_refreshed',
  TOKEN_EXPIRED = 'token_expired',
  TOKEN_CLEARED = 'token_cleared'
}

/**
 * Enhanced service for handling JWT token storage, retrieval, and expiration
 * Uses event emitter pattern to notify subscribers of token changes
 */
class TokenService extends EventEmitter {
  /**
   * Stores authentication tokens in localStorage with expiry
   */
  public setTokens(authResponse: AuthResponse): void {
    try {
      const { accessToken, refreshToken, user } = authResponse;
      
      // Calculate expiry timestamps
      const accessTokenExpiresAt = Date.now() + env.ACCESS_TOKEN_EXPIRY * 1000;
      const refreshTokenExpiresAt = Date.now() + env.REFRESH_TOKEN_EXPIRY * 1000;
      
      // Store tokens securely
      LocalStorageService.setItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN, accessToken, true);
      LocalStorageService.setItem(LOCAL_STORAGE_KEYS.REFRESH_TOKEN, refreshToken, true);
      LocalStorageService.setItem(LOCAL_STORAGE_KEYS.USER, user);
      
      // Store expiry timestamps
      LocalStorageService.setItem(LOCAL_STORAGE_KEYS.EXPIRES_AT, {
        accessTokenExpiresAt,
        refreshTokenExpiresAt
      });
      
      // Emit token stored event
      this.emit(TokenEventType.TOKEN_STORED, { user });
      
      logger.debug('TokenService: Tokens stored successfully');
    } catch (error) {
      logger.error('TokenService: Failed to store tokens', error);
      throw new Error('Failed to store authentication tokens');
    }
  }

  /**
   * Retrieves all token data with validation
   */
  public getTokens(): TokenData | null {
    try {
      const accessToken = LocalStorageService.getItem<string>(LOCAL_STORAGE_KEYS.ACCESS_TOKEN, false, true);
      const refreshToken = LocalStorageService.getItem<string>(LOCAL_STORAGE_KEYS.REFRESH_TOKEN, false, true);
      const expiryData = LocalStorageService.getItem<{
        accessTokenExpiresAt: number;
        refreshTokenExpiresAt: number;
      }>(LOCAL_STORAGE_KEYS.EXPIRES_AT);
      
      if (!accessToken || !refreshToken || !expiryData) {
        logger.debug('TokenService: Incomplete token data found');
        return null;
      }
      
      const { accessTokenExpiresAt, refreshTokenExpiresAt } = expiryData;
      
      // Emit token retrieved event
      this.emit(TokenEventType.TOKEN_RETRIEVED);
      
      return {
        accessToken,
        refreshToken,
        accessTokenExpiresAt,
        refreshTokenExpiresAt
      };
    } catch (error) {
      logger.error('TokenService: Failed to retrieve tokens', error);
      return null;
    }
  }

  /**
   * Checks if the access token has expired
   */
  public isAccessTokenExpired(): boolean {
    try {
      const expiryData = LocalStorageService.getItem<{
        accessTokenExpiresAt: number;
      }>(LOCAL_STORAGE_KEYS.EXPIRES_AT);
      
      if (!expiryData) {
        logger.debug('TokenService: No expiry data found');
        return true;
      }
      
      const isExpired = Date.now() > expiryData.accessTokenExpiresAt;
      
      if (isExpired) {
        this.emit(TokenEventType.TOKEN_EXPIRED, { tokenType: 'access' });
      }
      
      return isExpired;
    } catch (error) {
      logger.error('TokenService: Error checking token expiry', error);
      return true;
    }
  }

  /**
   * Checks if the refresh token has expired
   */
  public isRefreshTokenExpired(): boolean {
    try {
      const expiryData = LocalStorageService.getItem<{
        refreshTokenExpiresAt: number;
      }>(LOCAL_STORAGE_KEYS.EXPIRES_AT);
      
      if (!expiryData) {
        logger.debug('TokenService: No refresh token expiry data found');
        return true;
      }
      
      const isExpired = Date.now() > expiryData.refreshTokenExpiresAt;
      
      if (isExpired) {
        this.emit(TokenEventType.TOKEN_EXPIRED, { tokenType: 'refresh' });
      }
      
      return isExpired;
    } catch (error) {
      logger.error('TokenService: Error checking refresh token expiry', error);
      return true;
    }
  }

  /**
   * Gets the access token if valid
   */
  public getAccessToken(): string | null {
    if (this.isAccessTokenExpired()) {
      logger.debug('TokenService: Access token is expired');
      return null;
    }
    
    return LocalStorageService.getItem<string>(LOCAL_STORAGE_KEYS.ACCESS_TOKEN, false, true);
  }

  /**
   * Gets the refresh token if valid
   */
  public getRefreshToken(): string | null {
    if (this.isRefreshTokenExpired()) {
      logger.debug('TokenService: Refresh token is expired');
      return null;
    }
    
    return LocalStorageService.getItem<string>(LOCAL_STORAGE_KEYS.REFRESH_TOKEN, false, true);
  }

  /**
   * Updates just the access token (after refresh)
   */
  public updateAccessToken(newAccessToken: string): void {
    try {
      // Store new access token
      LocalStorageService.setItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN, newAccessToken, true);
      
      // Update expiry
      const expiryData = LocalStorageService.getItem<{
        accessTokenExpiresAt: number;
        refreshTokenExpiresAt: number;
      }>(LOCAL_STORAGE_KEYS.EXPIRES_AT) || {
        refreshTokenExpiresAt: Date.now() + env.REFRESH_TOKEN_EXPIRY * 1000
      };
      
      const updatedExpiryData = {
        ...expiryData,
        accessTokenExpiresAt: Date.now() + env.ACCESS_TOKEN_EXPIRY * 1000
      };
      
      LocalStorageService.setItem(LOCAL_STORAGE_KEYS.EXPIRES_AT, updatedExpiryData);
      
      // Emit token refreshed event
      this.emit(TokenEventType.TOKEN_REFRESHED);
      
      logger.debug('TokenService: Access token updated successfully');
    } catch (error) {
      logger.error('TokenService: Failed to update access token', error);
      throw new Error('Failed to update access token');
    }
  }

  /**
   * Clears all authentication tokens and related data
   */
  public clearTokens(): void {
    try {
      LocalStorageService.removeItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN);
      LocalStorageService.removeItem(LOCAL_STORAGE_KEYS.REFRESH_TOKEN);
      LocalStorageService.removeItem(LOCAL_STORAGE_KEYS.EXPIRES_AT);
      LocalStorageService.removeItem(LOCAL_STORAGE_KEYS.USER);
      
      // Emit token cleared event
      this.emit(TokenEventType.TOKEN_CLEARED);
      
      logger.debug('TokenService: Tokens cleared successfully');
    } catch (error) {
      logger.error('TokenService: Failed to clear tokens', error);
    }
  }

  /**
   * Get the stored user from local storage
   */
  public getStoredUser<T>(): T | null {
    return LocalStorageService.getItem<T>(LOCAL_STORAGE_KEYS.USER);
  }
}

// Export as singleton instance
export const tokenService = new TokenService();
```

```typescript
// src/services/token/tokenInterceptor.ts
import { tokenService } from './tokenService';
import { logger } from '../../middleware/logger';
import { HTTP

## 4. Enterprise-Level Logger

Create a configurable logger for enterprise-level logging:

```typescript
// src/middleware/logger.ts
import { env } from '../config/environment';

type LogMethod = (...args: any[]) => void;

interface LoggerInterface {
  debug: LogMethod;
  info: LogMethod;
  warn: LogMethod;
  error: LogMethod;
}

/**
 * Enterprise-level logger with configurable log levels
 * Can be extended to integrate with monitoring services like Sentry, LogRocket, etc.
 */
class Logger implements LoggerInterface {
  private readonly LOG_LEVELS = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3
  };

  private currentLogLevel: number;

  constructor() {
    this.currentLogLevel = this.LOG_LEVELS[env.LOG_LEVEL];
  }

  /**
   * Formats log messages consistently with timestamps and context
   */
  private formatLogMessage(level: string, ...args: any[]): string {
    const timestamp = new Date().toISOString();
    const context = args[0] && typeof args[0] === 'string' ? args.shift() : '';
    
    return `[${timestamp}] [${level.toUpperCase()}] ${context} ${args.map(arg => 
      typeof arg === 'object' ? JSON.stringify(arg) : arg
    ).join(' ')}`;
  }

  /**
   * Logs debug messages
   */
  public debug(...args: any[]): void {
    if (this.currentLogLevel <= this.LOG_LEVELS.debug) {
      console.debug(this.formatLogMessage('debug', ...args));
    }
  }

  /**
   * Logs info messages
   */
  public info(...args: any[]): void {
    if (this.currentLogLevel <= this.LOG_LEVELS.info) {
      console.info(this.formatLogMessage('info', ...args));
    }
  }

  /**
   * Logs warning messages
   */
  public warn(...args: any[]): void {
    if (this.currentLogLevel <= this.LOG_LEVELS.warn) {
      console.warn(this.formatLogMessage('warn', ...args));
    }
  }

  /**
   * Logs error messages
   */
  public error(...args: any[]): void {
    if (this.currentLogLevel <= this.LOG_LEVELS.error) {
      console.error(this.formatLogMessage('error', ...args));
      
      // In a real enterprise app, you would integrate with error monitoring services
      // Example: Sentry.captureException(args[args.length - 1]);
    }
  }
}

// Export as singleton
export const logger = new Logger();
```

## 5. Performance Monitoring Middleware

Create middleware to monitor Redux actions and performance:

```typescript
// src/middleware/performanceMonitoring.ts
import { Middleware } from '@reduxjs/toolkit';
import { env } from '../config/environment';
import { logger } from './logger';

/**
 * Redux middleware for performance monitoring of actions
 */
export const performanceMonitoringMiddleware: Middleware = store => next => action => {
  if (!env.PERFORMANCE_MONITORING) {
    return next(action);
  }
  
  // Log action type and payload
  logger.debug('Action', { type: action.type, payload: action.payload });
  
  // Measure execution time
  const startTime = performance.now();
  const result = next(action);
  const endTime = performance.now();
  const duration = endTime - startTime;
  
  // Log performance data
  logger.debug('Performance', { 
    action: action.type, 
    duration: `${duration.toFixed(2)}ms`,
    timestamp: new Date().toISOString()
  });

  // For slow actions, log a warning
  if (duration > 100) { // 100ms threshold
    logger.warn('Slow action detected', { 
      action: action.type, 
      duration: `${duration.toFixed(2)}ms`
    });
  }
  
  return result;
};
```

## 6. Authentication API with RTK Query

Create an RTK Query service for authentication:

```typescript
// src/features/auth/authApi.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { env } from '../../config/environment';
import { 
  AuthResponse, 
  LoginRequest, 
  RefreshTokenRequest, 
  RegisterRequest 
} from '../../types';
import { tokenService } from '../../services/tokenService';
import { logger } from '../../middleware/logger';

/**
 * RTK Query API for authentication endpoints
 */
export const authApi = createApi({
  reducerPath: 'authApi',
  baseQuery: fetchBaseQuery({ 
    baseUrl: `${env.API_URL}/auth`,
    prepareHeaders: (headers) => {
      // Add auth token to headers for protected endpoints
      const token = tokenService.getAccessToken();
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      return headers;
    }
  }),
  endpoints: (builder) => ({
    login: builder.mutation<AuthResponse, LoginRequest>({
      query: (credentials) => ({
        url: '/login',
        method: 'POST',
        body: credentials,
      }),
      // Handle successful login
      onQueryStarted: async (_, { queryFulfilled }) => {
        try {
          const { data } = await queryFulfilled;
          tokenService.setTokens(data);
          logger.info('User logged in successfully');
        } catch (error) {
          logger.error('Login failed', error);
        }
      },
    }),
    
    register: builder.mutation<AuthResponse, RegisterRequest>({
      query: (userData) => ({
        url: '/register',
        method: 'POST',
        body: userData,
      }),
      // Handle successful registration
      onQueryStarted: async (_, { queryFulfilled }) => {
        try {
          const { data } = await queryFulfilled;
          tokenService.setTokens(data);
          logger.info('User registered successfully');
        } catch (error) {
          logger.error('Registration failed', error);
        }
      },
    }),
    
    refreshToken: builder.mutation<AuthResponse, RefreshTokenRequest>({
      query: (refreshData) => ({
        url: '/refresh',
        method: 'POST',
        body: refreshData,
      }),
      // Handle token refresh
      onQueryStarted: async (_, { queryFulfilled }) => {
        try {
          const { data } = await queryFulfilled;
          tokenService.setTokens(data);
          logger.info('Token refreshed successfully');
        } catch (error) {
          logger.error('Token refresh failed', error);
          // Force logout on refresh failure
          tokenService.clearTokens();
        }
      },
    }),
    
    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/logout',
        method: 'POST',
      }),
      // Handle logout
      onQueryStarted: async (_, { queryFulfilled }) => {
        try {
          await queryFulfilled;
          tokenService.clearTokens();
          logger.info('User logged out successfully');
        } catch (error) {
          logger.error('Logout failed', error);
          // Force logout anyway
          tokenService.clearTokens();
        }
      },
    }),
    
    // Verify token validity
    verifyToken: builder.query<{ valid: boolean }, void>({
      query: () => '/verify',
    }),
  }),
});

// Export hooks for using the API
export const { 
  useLoginMutation,
  useRegisterMutation,
  useRefreshTokenMutation,
  useLogoutMutation,
  useVerifyTokenQuery
} = authApi;
```

## 7. Auth Slice for Managing Authentication State

Create a Redux slice to manage authentication state:

```typescript
// src/features/auth/authSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { User } from '../../types';
import { authApi } from './authApi';
import { tokenService } from '../../services/tokenService';
import { RootState } from '../../app/store';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: Boolean(tokenService.getAccessToken()),
  isLoading: false,
  error: null,
};

/**
 * Redux slice for managing authentication state
 */
export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
      state.isAuthenticated = true;
      state.error = null;
    },
    clearCredentials: (state) => {
      state.user = null;
      state.isAuthenticated = false;
      state.error = null;
      tokenService.clearTokens();
    },
    setAuthError: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
    },
  },
  // Handle RTK Query response lifecycle
  extraReducers: (builder) => {
    builder
      // Login
      .addMatcher(
        authApi.endpoints.login.matchPending,
        (state) => {
          state.isLoading = true;
          state.error = null;
        }
      )
      .addMatcher(
        authApi.endpoints.login.matchFulfilled,
        (state, { payload }) => {
          state.isLoading = false;
          state.isAuthenticated = true;
          state.user = payload.user;
        }
      )
      .addMatcher(
        authApi.endpoints.login.matchRejected,
        (state, { error }) => {
          state.isLoading = false;
          state.error = error.message || 'Authentication failed';
        }
      )
      
      // Registration
      .addMatcher(
        authApi.endpoints.register.matchPending,
        (state) => {
          state.isLoading = true;
          state.error = null;
        }
      )
      .addMatcher(
        authApi.endpoints.register.matchFulfilled,
        (state, { payload }) => {
          state.isLoading = false;
          state.isAuthenticated = true;
          state.user = payload.user;
        }
      )
      .addMatcher(
        authApi.endpoints.register.matchRejected,
        (state, { error }) => {
          state.isLoading = false;
          state.error = error.message || 'Registration failed';
        }
      )
      
      // Logout
      .addMatcher(
        authApi.endpoints.logout.matchFulfilled,
        (state) => {
          state.user = null;
          state.isAuthenticated = false;
          state.error = null;
        }
      );
  },
});

// Export actions
export const { setCredentials, clearCredentials, setAuthError } = authSlice.actions;

// Export selectors
export const selectCurrentUser = (state: RootState) => state.auth.user;
export const selectIsAuthenticated = (state: RootState) => state.auth.isAuthenticated;
export const selectAuthError = (state: RootState) => state.auth.error;
export const selectAuthLoading = (state: RootState) => state.auth.isLoading;

export default authSlice.reducer;
```

## 8. User CRUD Operations with RTK Query

Create an API service for user operations:

```typescript
// src/features/users/usersApi.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { env } from '../../config/environment';
import { User, UpdateUserRequest, ChangePasswordRequest } from '../../types';
import { tokenService } from '../../services/tokenService';
import { logger } from '../../middleware/logger';

/**
 * RTK Query API for user management endpoints
 */
export const usersApi = createApi({
  reducerPath: 'usersApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${env.API_URL}/users`,
    prepareHeaders: (headers) => {
      const token = tokenService.getAccessToken();
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['User'],
  endpoints: (builder) => ({
    // Get current user profile
    getProfile: builder.query<User, void>({
      query: () => '/me',
      providesTags: ['User'],
    }),
    
    // Update user profile
    updateProfile: builder.mutation<User, UpdateUserRequest>({
      query: (userData) => ({
        url: '/me',
        method: 'PATCH',
        body: userData,
      }),
      invalidatesTags: ['User'],
      // Log success or failure
      onQueryStarted: async (_, { queryFulfilled }) => {
        try {
          await queryFulfilled;
          logger.info('User profile updated successfully');
        } catch (error) {
          logger.error('Profile update failed', error);
        }
      },
    }),
    
    // Change password
    changePassword: builder.mutation<void, ChangePasswordRequest>({
      query: (passwordData) => ({
        url: '/me/password',
        method: 'POST',
        body: passwordData,
      }),
      // Log success or failure
      onQueryStarted: async (_, { queryFulfilled }) => {
        try {
          await queryFulfilled;
          logger.info('Password changed successfully');
        } catch (error) {
          logger.error('Password change failed', error);
        }
      },
    }),
    
    // Delete account
    deleteAccount: builder.mutation<void, void>({
      query: () => ({
        url: '/me',
        method: 'DELETE',
      }),
      // Log and handle account deletion
      onQueryStarted: async (_, { queryFulfilled }) => {
        try {
          await queryFulfilled;
          tokenService.clearTokens();
          logger.info('Account deleted successfully');
        } catch (error) {
          logger.error('Account deletion failed', error);
        }
      },
    }),
    
    // Admin only: Get all users
    getAllUsers: builder.query<User[], void>({
      query: () => '/',
      providesTags: ['User'],
    }),
    
    // Admin only: Get user by ID
    getUserById: builder.query<User, string>({
      query: (id) => `/${id}`,
      providesTags: (_, __, id) => [{ type: 'User', id }],
    }),
    
    // Admin only: Update user by ID
    updateUser: builder.mutation<User, { id: string; data: UpdateUserRequest }>({
      query: ({ id, data }) => ({
        url: `/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (_, __, arg) => [{ type: 'User', id: arg.id }, 'User'],
    }),
    
    // Admin only: Delete user by ID
    deleteUser: builder.mutation<void, string>({
      query: (id) => ({
        url: `/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['User'],
    }),
  }),
});

// Export hooks for using the API
export const {
  useGetProfileQuery,
  useUpdateProfileMutation,
  useChangePasswordMutation,
  useDeleteAccountMutation,
  useGetAllUsersQuery,
  useGetUserByIdQuery,
  useUpdateUserMutation,
  useDeleteUserMutation,
} = usersApi;
```

## 9. Redux Store Configuration

Configure the Redux store with persistence:

```typescript
// src/app/store.ts
import { configureStore, combineReducers } from '@reduxjs/toolkit';
import { 
  persistReducer, 
  persistStore,
  FLUSH,
  REHYDRATE,
  PAUSE,
  PERSIST,
  PURGE,
  REGISTER
} from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import { setupListeners } from '@reduxjs/toolkit/query';

import authReducer from '../features/auth/authSlice';
import { authApi } from '../features/auth/authApi';
import { usersApi } from '../features/users/usersApi';
import { performanceMonitoringMiddleware } from '../middleware/performanceMonitoring';
import { logger } from '../middleware/logger';

// Configure persistence
const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['auth'], // Only persist auth state
};

const rootReducer = combineReducers({
  auth: authReducer,
  [authApi.reducerPath]: authApi.reducer,
  [usersApi.reducerPath]: usersApi.reducer,
});

const persistedReducer = persistReducer(persistConfig, rootReducer);

/**
 * Configure Redux store with middleware and persistence
 */
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
      },
    })
      .concat(authApi.middleware)
      .concat(usersApi.middleware)
      .concat(performanceMonitoringMiddleware),
});

// Create persisted store
export const persistor = persistStore(store);

// Enable refetchOnFocus and refetchOnReconnect
setupListeners(store.dispatch);

// Log store initialization
logger.info('Redux store initialized');

// Export types
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

## 10. Custom Redux Hooks

Create type-safe hooks for accessing the Redux store:

```typescript
// src/app/hooks.ts
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from './store';

/**
 * Type-safe versions of useDispatch and useSelector hooks
 */
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
```

## 11. Implementing Authentication in App.tsx

Here's how to use the authentication system in your main App component:

```typescript
// src/App.tsx
import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from './app/hooks';
import { 
  selectIsAuthenticated, 
  selectCurrentUser, 
  clearCredentials 
} from './features/auth/authSlice';
import { 
  useRefreshTokenMutation, 
  useVerifyTokenQuery 
} from './features/auth/authApi';
import { tokenService } from './services/tokenService';
import { logger } from './middleware/logger';

const App: React.FC = () => {
  const dispatch = useAppDispatch();
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  const currentUser = useAppSelector(selectCurrentUser);
  
  const [refreshToken] = useRefreshTokenMutation();
  
  // Check token validity and refresh if needed
  useEffect(() => {
    const checkTokenValidity = async () => {
      if (isAuthenticated) {
        if (tokenService.isTokenExpired()) {
          logger.info('Access token expired, attempting refresh');
          const refreshTokenValue = tokenService.getRefreshToken();
          
          if (refreshTokenValue) {
            try {
              await refreshToken({ refreshToken: refreshTokenValue }).unwrap();
              logger.info('Token refreshed successfully');
            } catch (error) {
              logger.error('Failed to refresh token', error);
              dispatch(clearCredentials());
            }
          } else {
            logger.warn('No refresh token available, logging out');
            dispatch(clearCredentials());
          }
        }
      }
    };
    
    checkTokenValidity();
    
    // Set up periodic token check
    const tokenCheckInterval = setInterval(checkTokenValidity, 60000); // Check every minute
    
    return () => {
      clearInterval(tokenCheckInterval);
    };
  }, [dispatch, isAuthenticated, refreshToken]);
  
  return (
    <div className="app">
      {isAuthenticated ? (
        <div>
          <p>Welcome, {currentUser?.firstName}!</p>
          {/* Protected app content */}
        </div>
      ) : (
        <div>
          {/* Login/Registration forms */}
        </div>
      )}
    </div>
  );
};

export default App;
```

## 12. Example Login Form Implementation

Here's a basic login form component using our authentication system:

```typescript
// src/components/LoginForm.tsx
import React, { useState } from 'react';
import { useLoginMutation } from '../features/auth/authApi';
import { selectAuthError } from '../features/auth/authSlice';
import { useAppSelector } from '../app/hooks';
import { logger } from '../middleware/logger';

const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  const [login, { isLoading }] = useLoginMutation();
  const authError = useAppSelector(selectAuthError);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await login({ email, password }).unwrap();
      logger.info('Login successful');
    } catch (error) {
      logger.error('Login error', error);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <h2>Login</h2>
      
      {authError && <div className="error">{authError}</div>}
      
      <div>
        <label htmlFor="email">Email</label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      
      <div>
        <label htmlFor="password">Password</label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
};

export default LoginForm;
```

## 13. Example User Profile Component

Here's a component for viewing and editing a user profile:

```typescript
// src/components/UserProfile.tsx
import React, { useState } from 'react';
import { useGetProfileQuery, useUpdateProfileMutation } from '../features/users/usersApi';
import { logger } from '../middleware/logger';

const UserProfile: React.FC = () => {
  const { data: user, isLoading, error } = useGetProfileQuery();
  const [updateProfile, { isLoading: isUpdating }] = useUpdateProfileMutation();
  
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: ''
  });
  
  // Initialize form when user data is loaded
  React.useEffect(() => {
    if (user) {
      setFormData({
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.email
      });
    }
  }, [user]);
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await updateProfile(formData).unwrap();
      setIsEditing(false);
      logger.info('Profile updated successfully');
    } catch (error) {
      logger.error('Failed to update profile', error);
    }
  };
  
  if (isLoading) return <div>Loading profile...</div