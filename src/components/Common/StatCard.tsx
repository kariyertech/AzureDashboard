import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  colorClass?: string;
  change?: { value: string; positive: boolean };
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, colorClass = '', change }) => (
  <div className={`flex items-center justify-between bg-white rounded-xl shadow-card px-6 py-5 min-w-[220px] ${colorClass}`}>
    <div>
      <div className="text-gray-500 font-medium text-sm mb-1 flex items-center gap-2">{title}</div>
      <div className="text-3xl font-extrabold text-gray-900">{value}</div>
      {change && (
        <div className={`text-xs mt-1 font-semibold flex items-center gap-1 ${change.positive ? 'text-green-600' : 'text-red-500'}`}>
          {change.positive ? '↑' : '↓'} {change.value}
        </div>
      )}
    </div>
    <div className="opacity-80">{icon}</div>
  </div>
);

export default StatCard;
