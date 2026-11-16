// format currency amount
export const formatCurrency = (val) => {
  if (val === null || val === undefined || isNaN(val)) return '$0.00'; // handle null zero
  return new Intl.NumberFormat('en-US', {
    style: 'currency', // currency style
    currency: 'USD', // us dollar
    minimumFractionDigits: 2, // two decimals
    maximumFractionDigits: 2 // max decimals
  }).format(val); // format string
};

// format integer number
export const formatNumber = (val) => {
  if (val === null || val === undefined || isNaN(val)) return '0'; // handle null zero
  return new Intl.NumberFormat('en-US').format(val); // comma formatted
};

// format percentage rate
export const formatPercent = (val) => {
  if (val === null || val === undefined || isNaN(val)) return '0.0%'; // handle null zero
  return `${Number(val).toFixed(1)}%`; // one decimal pct
};

// format short date
export const formatDate = (dateStr) => {
  if (!dateStr) return '-'; // empty placeholder
  try {
    const d = new Date(dateStr); // parse date object
    return d.toLocaleDateString('en-US', {
      month: 'short', // short month
      day: 'numeric', // numeric day
      year: 'numeric' // full year
    });
  } catch (e) {
    return dateStr; // fallback raw
  }
};

// format byte size
export const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'; // empty byte size
  const k = 1024; // kilobyte factor
  const sizes = ['B', 'KB', 'MB', 'GB']; // size units
  const i = Math.floor(Math.log(bytes) / Math.log(k)); // unit index
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`; // formatted size
};
