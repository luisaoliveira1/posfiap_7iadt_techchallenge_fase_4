import axios from 'axios'
import type { AnalysisResult } from '../types/analysis'
import type { Review, ReviewDecisionPayload } from '../types/review'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 300000,
})

export async function analyzeAudio(file: File): Promise<AnalysisResult> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await client.post<AnalysisResult>('/api/audio/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function analyzeText(text: string): Promise<AnalysisResult> {
  const { data } = await client.post<AnalysisResult>('/api/audio/analyze-text', { text })
  return data
}

export async function submitDecision(jobId: string, payload: ReviewDecisionPayload): Promise<Review> {
  const { data } = await client.post<Review>(`/api/reviews/${jobId}/decide`, payload)
  return data
}
