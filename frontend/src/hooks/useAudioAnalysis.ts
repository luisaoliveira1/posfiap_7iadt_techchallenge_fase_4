import { useState } from 'react'
import { analyzeAudio, analyzeText } from '../services/api'
import type { AnalysisState } from '../types/analysis'

export function useAudioAnalysis() {
  const [state, setState] = useState<AnalysisState>({ status: 'idle' })

  async function submitAudio(file: File) {
    setState({ status: 'uploading' })
    try {
      const result = await analyzeAudio(file)
      setState({ status: 'done', result })
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Erro ao analisar o áudio. Tente novamente.'
      setState({ status: 'error', message: msg })
    }
  }

  async function submitText(text: string) {
    setState({ status: 'uploading' })
    try {
      const result = await analyzeText(text)
      setState({ status: 'done', result })
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Erro ao analisar o texto. Tente novamente.'
      setState({ status: 'error', message: msg })
    }
  }

  function reset() {
    setState({ status: 'idle' })
  }

  return { state, submitAudio, submitText, reset }
}
