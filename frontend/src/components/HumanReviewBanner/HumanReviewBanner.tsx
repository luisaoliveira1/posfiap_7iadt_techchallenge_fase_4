import styles from './HumanReviewBanner.module.css'

export function HumanReviewBanner() {
  return (
    <div className={styles.banner} role="alert">
      <span className={styles.icon}>⚠️</span>
      <div>
        <p className={styles.title}>Revisão humana recomendada</p>
        <p className={styles.sub}>
          Este caso foi encaminhado para revisão por um profissional de saúde via Azure AI Foundry.
        </p>
      </div>
    </div>
  )
}
