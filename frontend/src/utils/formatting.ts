/**
 * Utility functions for formatting numbers consistently.
 * All values should be displayed with 2 decimal places (or integers where appropriate).
 */

/**
 * Format a number to 2 decimal places.
 * @param value - Number to format
 * @returns Formatted string with 2 decimal places
 */
export function formatTo2Decimals(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  return value.toFixed(2);
}

/**
 * Format a number as a percentage with 2 decimal places.
 * @param value - Number to format (0.15 = 15%)
 * @returns Formatted string like "+15.00%" or "-15.00%"
 */
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  const sign = value >= 0 ? '+' : '';
  return `${sign}${(value * 100).toFixed(2)}%`;
}

/**
 * Format a number as a percentage with 2 decimal places (value already in percent).
 * @param value - Number already in percent (15 = 15%)
 * @returns Formatted string like "+15.00%" or "-15.00%"
 */
export function formatPercentValue(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * Format a number to integer (for counts, scores, etc.).
 * @param value - Number to format
 * @returns Formatted string as integer
 */
export function formatInteger(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  return Math.round(value).toString();
}

/**
 * Format currency in crores (Indian format).
 * @param value - Amount in rupees
 * @returns Formatted string like "₹123.45 Cr"
 */
export function formatCrores(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  const crores = value / 10000000;
  return `₹${crores.toFixed(2)} Cr`;
}

/**
 * Format a number with specified decimal places (default 2).
 * @param value - Number to format
 * @param decimals - Number of decimal places (default 2)
 * @returns Formatted string
 */
export function formatNumber(value: number | null | undefined, decimals: number = 2): string {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  return value.toFixed(decimals);
}

