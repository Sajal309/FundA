import { useMemo } from 'react';

export interface DataFreshnessProps {
  /** ISO timestamp string of when data was last updated */
  lastUpdated?: string | null;
  /** ISO timestamp string of when data was fetched (if different from lastUpdated) */
  fetchedAt?: string | null;
  /** Whether data is live (real-time) or cached */
  isLive?: boolean;
  /** Data source description (e.g., "Market data", "Sector rotation") */
  source?: string;
  /** Refresh interval in milliseconds (for auto-refresh indication) */
  refreshInterval?: number;
  /** Compact mode for smaller displays */
  compact?: boolean;
  /** Custom className */
  className?: string;
}

/**
 * Component to display data freshness information.
 * Shows when data was last updated, whether it's live or cached,
 * and auto-refresh status if applicable.
 */
export default function DataFreshness({
  lastUpdated,
  fetchedAt,
  isLive = false,
  source,
  refreshInterval,
  compact = false,
  className = '',
}: DataFreshnessProps) {
  const freshnessInfo = useMemo(() => {
    const timestamp = fetchedAt || lastUpdated;
    if (!timestamp) return null;

    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      let timeAgo: string;
      if (diffMins < 1) {
        timeAgo = 'Just now';
      } else if (diffMins < 60) {
        timeAgo = `${diffMins} min${diffMins !== 1 ? 's' : ''} ago`;
      } else if (diffHours < 24) {
        timeAgo = `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
      } else if (diffDays < 7) {
        timeAgo = `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
      } else {
        timeAgo = date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
        });
      }

      const formattedTime = date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      });

      return {
        timeAgo,
        formattedTime,
        formattedDate: date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        }),
        isStale: diffMins > (refreshInterval ? refreshInterval / 60000 : 30),
      };
    } catch (e) {
      return null;
    }
  }, [lastUpdated, fetchedAt, refreshInterval]);

  if (!freshnessInfo) {
    return null;
  }

  if (compact) {
    return (
      <div className={`flex items-center gap-2 text-xs text-dark-400 ${className}`}>
        <span className="flex items-center gap-1">
          {isLive ? (
            <>
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span>Live</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 bg-yellow-500 rounded-full" />
              <span>Cached</span>
            </>
          )}
        </span>
        <span className="text-dark-500">•</span>
        <span>{freshnessInfo.timeAgo}</span>
      </div>
    );
  }

  return (
    <div className={`flex flex-col gap-1 text-xs text-dark-400 ${className}`}>
      <div className="flex items-center gap-2">
        <span className="flex items-center gap-1.5">
          {isLive ? (
            <>
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" title="Live data" />
              <span className="font-medium text-green-400">Live</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 bg-yellow-500 rounded-full" title="Cached data" />
              <span className="font-medium text-yellow-400">Cached</span>
            </>
          )}
        </span>
        {source && (
          <>
            <span className="text-dark-500">•</span>
            <span>{source}</span>
          </>
        )}
      </div>
      <div className="flex items-center gap-2 text-dark-500">
        <span>Updated {freshnessInfo.timeAgo}</span>
        <span>•</span>
        <span title={`${freshnessInfo.formattedDate} at ${freshnessInfo.formattedTime}`}>
          {freshnessInfo.formattedTime}
        </span>
        {refreshInterval && (
          <>
            <span>•</span>
            <span>Auto-refresh: {Math.floor(refreshInterval / 60000)} min</span>
          </>
        )}
      </div>
      {freshnessInfo.isStale && (
        <div className="text-yellow-500 text-xs mt-1">
          ⚠️ Data may be stale. Consider refreshing.
        </div>
      )}
    </div>
  );
}

