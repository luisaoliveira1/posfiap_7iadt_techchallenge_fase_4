import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import type { TopicSignal } from '../../types/analysis'
import styles from './TopicSignals.module.css'

interface Props {
  signals: TopicSignal[]
}

const COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe']

export function TopicSignals({ signals }: Props) {
  if (!signals.length) return null

  const data = signals.map((s) => ({
    name: s.label.replace(/_/g, ' '),
    score: Math.round(s.score * 100),
  }))

  return (
    <div className={styles.container}>
      <h4 className={styles.title}>Sinais detectados</h4>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} layout="vertical" margin={{ left: 16, right: 16 }}>
          <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 12 }} />
          <YAxis type="category" dataKey="name" width={160} tick={{ fontSize: 12 }} />
          <Tooltip formatter={(v: number) => [`${v}%`, 'Score']} />
          <Bar dataKey="score" radius={[0, 4, 4, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
