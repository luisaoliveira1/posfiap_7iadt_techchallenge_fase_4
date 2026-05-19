import type { RiskLevel } from './analysis'

export type ReviewStatus = 'pending' | 'reviewed'
export type ReviewDecisionType = 'confirmed' | 'overridden'

export interface Review {
  job_id: string
  transcript: string
  risk_level: RiskLevel
  risk_level_display: string
  confidence: number
  probabilities: Record<RiskLevel, number>
  review_status: ReviewStatus
  reviewer_decision?: ReviewDecisionType
  reviewer_label?: RiskLevel
  reviewer_note?: string
  enqueued_at: string
  reviewed_at?: string
}

export interface ReviewDecisionPayload {
  decision: ReviewDecisionType
  label?: RiskLevel
  note?: string
}
