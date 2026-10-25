import React, { useRef, useEffect } from 'react';
import {
  PlayCircle,
  StopCircle,
  CheckCircle,
  FileText,
  DollarSign
} from 'lucide-react';
import type { TradeEvent } from '../types';
import { formatCurrency, formatTime } from '../utils/format';
import './EventTimeline.css';

interface Props {
  events: TradeEvent[];
  currentIndex: number;
}

export const EventTimeline: React.FC<Props> = ({ events, currentIndex }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const activeItemRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (activeItemRef.current && containerRef.current) {
      activeItemRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [currentIndex]);

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'session_started':
        return <PlayCircle size={16} className="ev-icon ev-icon--start" />;
      case 'session_ended':
        return <StopCircle size={16} className="ev-icon ev-icon--end" />;
      case 'order_submitted':
        return <FileText size={16} className="ev-icon ev-icon--order" />;
      case 'order_filled':
        return <CheckCircle size={16} className="ev-icon ev-icon--fill" />;
      case 'trade_closed':
        return <DollarSign size={16} className="ev-icon ev-icon--trade" />;
      default:
        return <FileText size={16} className="ev-icon" />;
    }
  };

  return (
    <div className="event-timeline" ref={containerRef}>
      <div className="event-timeline__header">
        <h4>Event Stream</h4>
        <span className="event-timeline__count">{events.length} events</span>
      </div>

      <div className="event-timeline__list">
        {events.length === 0 ? (
          <div className="timeline-empty">Waiting for simulation to start...</div>
        ) : (
          events.map((ev, idx) => {
            const isCurrent = idx === currentIndex - 1;
            const isFuture = idx >= currentIndex;

            return (
              <div
                key={ev.id || `${ev.event_id}-${idx}`}
                ref={isCurrent ? activeItemRef : null}
                className={`timeline-item ${isCurrent ? 'timeline-item--current' : ''} ${
                  isFuture ? 'timeline-item--future' : ''
                }`}
              >
                <div className="timeline-item__marker">
                  {getEventIcon(ev.event_type)}
                  {idx < events.length - 1 && <div className="timeline-item__line" />}
                </div>

                <div className="timeline-item__content">
                  <div className="timeline-item__top">
                    <span className="timeline-item__type">
                      {ev.event_type.replace(/_/g, ' ')}
                    </span>
                    <span className="timeline-item__time">{formatTime(ev.timestamp)}</span>
                  </div>

                  <div className="timeline-item__details">
                    <span className="timeline-badge instrument">{ev.instrument}</span>
                    {ev.side && (
                      <span className={`timeline-badge side side--${ev.side.toLowerCase()}`}>
                        {ev.side}
                      </span>
                    )}
                    {ev.quantity && (
                      <span className="timeline-detail">Qty: {ev.quantity}</span>
                    )}
                    {ev.price && (
                      <span className="timeline-detail">@{ev.price}</span>
                    )}
                    {ev.realized_pnl !== null && ev.realized_pnl !== undefined && (
                      <span
                        className={`timeline-pnl ${
                          ev.realized_pnl >= 0 ? 'pnl--pos' : 'pnl--neg'
                        }`}
                      >
                        {ev.realized_pnl >= 0 ? '+' : ''}
                        {formatCurrency(ev.realized_pnl)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
