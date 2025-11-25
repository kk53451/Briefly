/**
 * Logger Utility
 * Provides conditional logging based on environment
 */

const isDev = __DEV__;

export const logger = {
  /**
   * Debug/info logs (only in development)
   */
  log: (...args: any[]) => {
    if (isDev) {
      console.log(...args);
    }
  },

  /**
   * Warning logs (only in development)
   */
  warn: (...args: any[]) => {
    if (isDev) {
      console.warn(...args);
    }
  },

  /**
   * Error logs (always logged, even in production)
   */
  error: (...args: any[]) => {
    console.error(...args);
  },

  /**
   * Info logs (only in development)
   */
  info: (...args: any[]) => {
    if (isDev) {
      console.info(...args);
    }
  },

  /**
   * Debug logs (only in development)
   */
  debug: (...args: any[]) => {
    if (isDev) {
      console.debug(...args);
    }
  },
};
