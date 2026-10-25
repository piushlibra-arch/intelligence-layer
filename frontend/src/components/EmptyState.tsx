import React from 'react';
import { Inbox } from 'lucide-react';
import './EmptyState.css';

interface Props {
  title?: string;
  message: string;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<Props> = ({
  title = 'No data',
  message,
  icon,
}) => (
  <div className="empty-state" role="status">
    <div className="empty-state__icon">{icon || <Inbox size={40} />}</div>
    <h3 className="empty-state__title">{title}</h3>
    <p className="empty-state__message">{message}</p>
  </div>
);
