import React from 'react';
import clsx from 'clsx';

interface CardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  headerAction?: React.ReactNode;
}

const Card: React.FC<CardProps> = ({ title, children, className, headerAction }) => {
  const hasHeader = title || headerAction;
  return (
    <div className={clsx("rounded-lg shadow-card overflow-hidden relative", className)}>
      {hasHeader && (
        <div className="border-b border-gray-200/0 px-5 py-4 flex justify-between items-center min-h-[32px]">
          {title && <h3 className="text-base font-medium text-gray-900">{title}</h3>}
          {headerAction && (
            <div className="ml-auto flex items-center">{headerAction}</div>
          )}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
};

export default Card;