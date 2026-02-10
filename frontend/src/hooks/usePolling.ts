import { useCallback } from 'react';
import { poll } from '../services/utils/polling';

/**
 * A hook that provides a reusable polling function.
 * This is a wrapper around the core polling utility for use in components.
 */
export const usePolling = () => {
  const pollWithCallback = useCallback(poll, []);

  return {
    poll: pollWithCallback
  };
};
