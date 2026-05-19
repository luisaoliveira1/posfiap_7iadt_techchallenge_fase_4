export type RiskLevel = 'HIGH_RISK' | 'MONITORING' | 'LOW_RISK'

export interface TopicSignal {
  label: string
  score: number
}

export interface AnalysisResult {
  job_id: string
  transcript: string
  risk_level: RiskLevel
  risk_level_display: string
  confidence: number
  human_review_required: boolean
  probabilities: Record<RiskLevel, number>
  top_signals: TopicSignal[]
  features: Record<string, number>
}

export type AnalysisState =
  | { status: 'idle' }
  | { status: 'uploading' }
  | { status: 'done'; result: AnalysisResult }
  | { status: 'error'; message: string }
