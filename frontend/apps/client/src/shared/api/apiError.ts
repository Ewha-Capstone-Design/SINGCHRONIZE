export type ApiError = {
  code: string;
  message: string;
};

export const isApiError = (error: unknown): error is ApiError =>
  typeof error === 'object' &&
  error !== null &&
  'code' in error &&
  'message' in error &&
  typeof (error as ApiError).code === 'string' &&
  typeof (error as ApiError).message === 'string';

export const getApiErrorMessage = (error: unknown, fallback = '오류가 발생했습니다.'): string => {
  if (isApiError(error)) return error.message;
  if (error instanceof Error) return error.message;
  return fallback;
};
