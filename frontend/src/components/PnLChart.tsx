import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid
} from 'recharts';
import type { TradeEvent } from '../types';
import { formatCurrency } from '../utils/format';

interface Props {
  events: TradeEvent[];
}

export const PnLChart: React.FC<Props> = ({ events }) => {
  // Aggregate cumulative PnL over events
  let cumulative = 0;
  let peak = 0;
  const data = events.map((ev, index) => {
    if (ev.realized_pnl) {
      cumulative += Number(ev.realized_pnl);
      if (cumulative > peak) peak = cumulative;
    }
    return {
      index: index + 1,
      name: `Ev ${index + 1}`,
      type: ev.event_type.replace(/_/g, ' '),
      pnl: cumulative,
      peak: peak,
    };
  });

  if (data.length === 0) {
    return (
      <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
        No P&L data yet. Start simulation replay.
      </div>
    );
  }

  const latestPnL = data[data.length - 1]?.pnl || 0;
  const isPositive = latestPnL >= 0;

  return (
    <div style={{ width: '100%', height: 220 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.6} />
          <XAxis
            dataKey="name"
            stroke="var(--text-muted)"
            fontSize={11}
            tickLine={false}
          />
          <YAxis
            stroke="var(--text-muted)"
            fontSize={11}
            tickLine={false}
            tickFormatter={(val) => `₹${val}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--bg-secondary)',
              borderColor: 'var(--border)',
              borderRadius: '6px',
              fontSize: '12px',
              color: 'var(--text-primary)'
            }}
            formatter={(val: any) => [formatCurrency(Number(val)), 'Session P&L']}
          />
          <ReferenceLine y={0} stroke="var(--text-muted)" strokeDasharray="2 2" />
          <Line
            type="monotone"
            dataKey="pnl"
            stroke={isPositive ? 'var(--accent-green)' : 'var(--accent-red)'}
            strokeWidth={2.5}
            dot={{ r: 3, fill: isPositive ? 'var(--accent-green)' : 'var(--accent-red)' }}
            activeDot={{ r: 5 }}
          />
          <Line
            type="monotone"
            dataKey="peak"
            stroke="var(--accent-yellow)"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
