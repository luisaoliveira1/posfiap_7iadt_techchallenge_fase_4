import { AudioUpload } from './components/AudioUpload/AudioUpload'
import { RiskResult } from './components/RiskResult/RiskResult'
import { useAudioAnalysis } from './hooks/useAudioAnalysis'
import styles from './App.module.css'

export default function App() {
  const { state, submitAudio, submitText, reset } = useAudioAnalysis()
  const isLoading = state.status === 'uploading'

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Análise de Depressão Pós-Parto</h1>
        <p className={styles.subtitle}>
          Envie o áudio de uma consulta ou cole o texto transcrito para análise de risco.
        </p>
      </header>

      <main className={styles.main}>
        {state.status !== 'done' && (
          <section className={styles.card}>
            {isLoading ? (
              <div className={styles.spinner}>
                <div className={styles.dot} />
                <p className={styles.spinnerText}>Analisando...</p>
              </div>
            ) : (
              <AudioUpload
                onFileSelect={submitAudio}
                onTextSubmit={submitText}
                disabled={isLoading}
              />
            )}
            {state.status === 'error' && (
              <p className={styles.error}>{state.message}</p>
            )}
          </section>
        )}

        {state.status === 'done' && (
          <section className={styles.card}>
            <RiskResult result={state.result} onReset={reset} />
          </section>
        )}
      </main>
    </div>
  )
}
