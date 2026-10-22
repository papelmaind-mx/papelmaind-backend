// F21: logger dev-only estructurado — reemplaza console.*
export const logger = {
  dev: (...args: unknown[]) => {
    if (import.meta.env.DEV) console.debug('[PMPOS]', ...args);
  },
};
