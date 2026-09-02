import React from 'react';
import './SeverityBadge.css';

const SeverityBadge = ({ severity }) => {
  let badgeClass = 'badge-normal';

  if (severity === 'Critical') {
    badgeClass = 'badge-critical';
  } else if (severity === 'Warning') {
    badgeClass = 'badge-warning';
  }

  return (
    <span className={`severity-badge ${badgeClass}`}>
      {severity}
    </span>
  );
};

export default SeverityBadge;
