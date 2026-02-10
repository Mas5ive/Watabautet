import { POLLING } from '../../constants';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const poll = async <T>(
  fn: () => Promise<{ data: T | null; shouldContinue: boolean }>,
  maxAttempts: number = POLLING.MAX_ATTEMPTS,
  delayMs: number = POLLING.DELAY_MS,
  timeoutMessage: string = 'POLLING TIMED OUT'
): Promise<T> => {
  for (let i = 0; i < maxAttempts; i++) {
    await delay(delayMs);
    const { data, shouldContinue } = await fn();
    if (data !== null) {
      return data;
    }
    if (!shouldContinue) {
      break;
    }
  }
  throw new Error(timeoutMessage);
};
