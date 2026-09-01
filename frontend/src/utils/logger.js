/**
 * Structured client-side logger.
 * Formats logs with timestamps, levels, and request-id tracing metadata.
 */

const LOG_LEVELS = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

class Logger {
  constructor() {
    this.level = 'info';
  }

  setLevel(level) {
    if (LOG_LEVELS[level] !== undefined) {
      this.level = level;
    }
  }

  _shouldLog(targetLevel) {
    return LOG_LEVELS[targetLevel] >= LOG_LEVELS[this.level];
  }

  _format(level, message, context = {}) {
    const timestamp = new Date().toISOString();
    const requestIdStr = context.requestId ? ` [request_id=${context.requestId}]` : '';
    return `${timestamp} | ${level.toUpperCase()}${requestIdStr} | ${message}`;
  }

  debug(message, context) {
    if (this._shouldLog('debug')) {
      console.debug(this._format('debug', message, context), context || '');
    }
  }

  info(message, context) {
    if (this._shouldLog('info')) {
      console.info(this._format('info', message, context), context || '');
    }
  }

  warn(message, context) {
    if (this._shouldLog('warn')) {
      console.warn(this._format('warn', message, context), context || '');
    }
  }

  error(message, context) {
    if (this._shouldLog('error')) {
      console.error(this._format('error', message, context), context || '');
    }
  }
}

export const logger = new Logger();
