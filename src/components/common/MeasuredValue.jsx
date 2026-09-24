import React from 'react';

const NO_DATA_TEXT = 'No measured data available';

/**
 * T-P11-054: any metric that has not actually been measured must render as
 * "No measured data available" rather than a fabricated/placeholder number.
 *
 * A value counts as "measured" only if it is not null/undefined and, for
 * numbers, not NaN. Do not pass 0 as a stand-in for "unmeasured" — 0 is a
 * legitimate measured value and will be displayed as-is.
 */
export default function MeasuredValue({ value, unit = '', style }) {
  const isMeasured =
    value !== null &&
    value !== undefined &&
    !(typeof value === 'number' && Number.isNaN(value)) &&
    value !== '';

  if (!isMeasured) {
    return (
      <span style={{ color: '#777', fontStyle: 'italic', fontSize: '13px', ...style }}>
        {NO_DATA_TEXT}
      </span>
    );
  }

  return (
    <span style={style}>
      {value}
      {unit}
    </span>
  );
}

export { NO_DATA_TEXT };
