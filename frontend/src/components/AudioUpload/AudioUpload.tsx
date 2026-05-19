import { useRef, useState, DragEvent, ChangeEvent } from 'react'
import styles from './AudioUpload.module.css'

interface Props {
  onFileSelect: (file: File) => void
  onTextSubmit: (text: string) => void
  disabled: boolean
}

export function AudioUpload({ onFileSelect, onTextSubmit, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [text, setText] = useState('')
  const [mode, setMode] = useState<'audio' | 'text'>('audio')

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onFileSelect(file)
  }

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) onFileSelect(file)
  }

  return (
    <div className={styles.container}>
      <div className={styles.tabs}>
        <button
          className={mode === 'audio' ? styles.activeTab : styles.tab}
          onClick={() => setMode('audio')}
        >
          Enviar Áudio
        </button>
        <button
          className={mode === 'text' ? styles.activeTab : styles.tab}
          onClick={() => setMode('text')}
        >
          Inserir Texto
        </button>
      </div>

      {mode === 'audio' ? (
        <div
          className={`${styles.dropZone} ${dragging ? styles.dragging : ''} ${disabled ? styles.disabled : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => !disabled && inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        >
          <span className={styles.icon}>🎙️</span>
          <p className={styles.hint}>
            Arraste um arquivo de áudio aqui ou clique para selecionar
          </p>
          <p className={styles.sub}>.wav — max 50MB</p>
          <input
            ref={inputRef}
            type="file"
            accept=".wav"
            onChange={handleChange}
            style={{ display: 'none' }}
            disabled={disabled}
          />
        </div>
      ) : (
        <div className={styles.textMode}>
          <textarea
            className={styles.textarea}
            placeholder="Cole ou digite aqui o texto da consulta em português..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={8}
            disabled={disabled}
          />
          <button
            className={styles.submitBtn}
            onClick={() => text.trim() && onTextSubmit(text)}
            disabled={disabled || !text.trim()}
          >
            Analisar Texto
          </button>
        </div>
      )}
    </div>
  )
}
