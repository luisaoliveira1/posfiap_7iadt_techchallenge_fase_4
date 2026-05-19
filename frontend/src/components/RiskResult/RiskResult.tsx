import { useState } from 'react'
import type { AnalysisResult, RiskLevel } from '../../types/analysis'
import { submitDecision } from '../../services/api'
import styles from './RiskResult.module.css'

interface Props {
  result: AnalysisResult
  onReset: () => void
}

const LEVEL_CONFIG: Record<RiskLevel, { color: string; bg: string; label: string }> = {
  HIGH_RISK: { color: '#dc2626', bg: '#fef2f2', label: 'Alto Risco' },
  MONITORING: { color: '#d97706', bg: '#fffbeb', label: 'Monitorar' },
  LOW_RISK: { color: '#16a34a', bg: '#f0fdf4', label: 'Baixo Risco' },
}

type FeedbackState = 'idle' | 'choosing' | 'submitting' | 'done' | 'error'

export function RiskResult({ result, onReset }: Props) {
  const cfg = LEVEL_CONFIG[result.risk_level] ?? LEVEL_CONFIG.LOW_RISK
  const pct = Math.round(result.confidence * 100)

  const [feedbackState, setFeedbackState] = useState<FeedbackState>('idle')
  const [feedbackError, setFeedbackError] = useState('')
  const [confirmingReset, setConfirmingReset] = useState(false)

  async function handleConfirm() {
    setFeedbackState('submitting')
    try {
      await submitDecision(result.job_id, { decision: 'confirmed', label: result.risk_level })
      setFeedbackState('done')
    } catch {
      setFeedbackError('Erro ao salvar feedback. Tente novamente.')
      setFeedbackState('error')
    }
  }

  async function handleOverride(label: RiskLevel) {
    setFeedbackState('submitting')
    try {
      await submitDecision(result.job_id, { decision: 'overridden', label })
      setFeedbackState('done')
    } catch {
      setFeedbackError('Erro ao salvar feedback. Tente novamente.')
      setFeedbackState('error')
    }
  }

  return (
    <div className={styles.container}>

      {/* Back button — always at the very top */}
      <div className={styles.backRow}>
        <button className={styles.backBtn} onClick={() => setConfirmingReset(true)}>
          ← Nova análise
        </button>
      </div>

      {confirmingReset && (
        <div className={styles.modalOverlay} onClick={() => setConfirmingReset(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <p className={styles.modalTitle}>Iniciar nova análise?</p>
            <p className={styles.modalText}>
              Os dados desta sessão não serão perdidos.
            </p>
            <div className={styles.modalActions}>
              <button className={styles.confirmYes} onClick={onReset}>Sim, nova análise</button>
              <button className={styles.confirmNo} onClick={() => setConfirmingReset(false)}>Cancelar</button>
            </div>
          </div>
        </div>
      )}

      <div className={styles.badge} style={{ background: cfg.bg, borderColor: cfg.color }}>
        <span className={styles.badgeLabel} style={{ color: cfg.color }}>{cfg.label}</span>
        <span className={styles.badgeSub}>{result.risk_level_display}</span>
      </div>

      <div className={styles.confidence}>
        <span className={styles.confidenceLabel}>Confiança: {pct}%</span>
        <div className={styles.bar}>
          <div
            className={styles.barFill}
            style={{ width: `${pct}%`, background: cfg.color }}
          />
        </div>
      </div>

      <div className={styles.probabilities}>
        <h4 className={styles.sectionTitle}>Probabilidades por nível</h4>
        {Object.entries(result.probabilities).map(([level, prob]) => {
          const c = LEVEL_CONFIG[level as RiskLevel]
          return (
            <div key={level} className={styles.probRow}>
              <span className={styles.probLabel} style={{ color: c?.color }}>
                {LEVEL_CONFIG[level as RiskLevel]?.label ?? level}
              </span>
              <div className={styles.probBar}>
                <div
                  className={styles.probFill}
                  style={{ width: `${Math.round(prob * 100)}%`, background: c?.color ?? '#6b7280' }}
                />
              </div>
              <span className={styles.probPct}>{Math.round(prob * 100)}%</span>
            </div>
          )
        })}
      </div>

      <div className={styles.transcript}>
        <h4 className={styles.sectionTitle}>Transcrição</h4>
        <blockquote className={styles.quote}>{result.transcript}</blockquote>
      </div>

      <div className={styles.feedback}>
        <h4 className={styles.sectionTitle}>Esta classificação está correta?</h4>

        {feedbackState === 'idle' && (
          <div className={styles.feedbackActions}>
            <button className={styles.feedbackConfirm} onClick={handleConfirm}>
              Sim, está correta
            </button>
            <button className={styles.feedbackOverride} onClick={() => setFeedbackState('choosing')}>
              Não, corrigir
            </button>
          </div>
        )}

        {feedbackState === 'choosing' && (
          <div className={styles.feedbackChoose}>
            <span className={styles.feedbackChooseLabel}>Qual deveria ser a classificação correta?</span>
            <div className={styles.feedbackActions}>
              {(Object.keys(LEVEL_CONFIG) as RiskLevel[]).map(level => (
                <button
                  key={level}
                  className={styles.feedbackLevel}
                  style={{ borderColor: LEVEL_CONFIG[level].color, color: LEVEL_CONFIG[level].color }}
                  disabled={level === result.risk_level}
                  onClick={() => handleOverride(level)}
                >
                  {LEVEL_CONFIG[level].label}
                </button>
              ))}
              <button className={styles.feedbackCancel} onClick={() => setFeedbackState('idle')}>
                Cancelar
              </button>
            </div>
          </div>
        )}

        {feedbackState === 'submitting' && (
          <p className={styles.feedbackPending}>Salvando feedback…</p>
        )}

        {feedbackState === 'done' && (
          <p className={styles.feedbackDone}>Feedback registrado. Obrigado!</p>
        )}

        {feedbackState === 'error' && (
          <p className={styles.feedbackErr}>{feedbackError}</p>
        )}
      </div>

    </div>
  )
}
