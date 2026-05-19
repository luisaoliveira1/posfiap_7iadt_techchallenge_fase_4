# Prompt para Geração de Áudios de Teste — Depressão Pós-Parto

Use este prompt com qualquer plataforma de Text-to-Speech (TTS) que suporte português brasileiro:
- **ElevenLabs** (voz "Bella" ou similar, pt-BR)
- **Azure Text-to-Speech** (voz `pt-BR-FranciscaNeural` ou `pt-BR-BrendaNeural`)
- **Google Cloud TTS** (voz `pt-BR-Wavenet-A`)
- **OpenAI TTS** (com instrução de idioma pt-BR)

---

## Configurações Recomendadas para Todas as Vozes

| Parâmetro        | Valor                  |
|-----------------|------------------------|
| Idioma           | pt-BR (Português Brasil) |
| Formato          | WAV, 16kHz, mono       |
| Duração alvo     | 90–120 segundos por arquivo |
| Tipo de voz      | Feminina, adulta        |

---

## Cenário 1 — ALTO RISCO (com ideação suicida)
**Arquivo:** `scenario_01_high_risk_ideacao.wav`
**Perfil:** Maria, 28 anos, 3 semanas pós-parto, primeiro filho

**Tom de voz:** Voz baixa, pausada, com breaks de silêncio entre frases. Choro
perceptível em algumas passagens. Falar devagar, quase sem energia. Evitar
entonação alegre em qualquer momento.

**Texto para TTS:**
```
Doutora, eu... eu não sei mais o que fazer.
[pausa 2s]
Eu não durmo. Quando o bebê chora, eu só quero sumir. Desaparecer.
Às vezes fico pensando que seria melhor se eu não estivesse aqui. Que eles
estariam melhor sem mim.
[pausa 1.5s]
Não consigo cuidar dele direito. Me sinto um fracasso total. Uma mãe horrível.
Não sinto nada quando ele sorri para mim. Absolutamente nada. É como se eu
estivesse vendo tudo de longe, sabe? Como se não fosse real.
[pausa 1s]
Meu marido tenta ajudar mas eu só consigo chorar e não sei nem por quê.
Choro o dia todo. De madrugada fico olhando para o teto sem conseguir dormir.
[pausa 1s]
Estou com medo de mim mesma, doutora. Com muito medo.
```

**Classificação esperada:** HIGH_RISK (alto risco) — `humanReviewRequired: true`

---

## Cenário 2 — ALTO RISCO (sem ideação suicida, mas severo)
**Arquivo:** `scenario_02_high_risk_severo.wav`
**Perfil:** Carla, 32 anos, 6 semanas pós-parto, segundo filho

**Tom de voz:** Monotônico, claramente exausto. Respostas curtas. Ritmo lento de
fala. Sem variação de entonação. Como alguém que está no automático.

**Texto para TTS:**
```
Doutora, eu não estou bem. Não consigo levantar da cama direito.
[pausa 1s]
Não tenho vontade de comer. De tomar banho. De nada mesmo.
Só faço o mínimo pelo bebê porque ele precisa de mim. Mas é como se eu
estivesse no piloto automático. Faço tudo sem sentir nada.
[pausa 1s]
Larguei de amamentar porque não aguentei mais. Me sinto muito culpada por isso.
Todo dia me sinto culpada por isso.
[pausa 1s]
Fico irritada com tudo. Com meu marido. Com minha mãe que fica tentando ajudar.
Com a minha filha mais velha que só quer atenção e eu não tenho nada para dar.
[pausa 1s]
Não consigo sentir alegria em nada. Nem quando vejo o bebê. Nem quando vejo
minha filha mais velha. Não sinto nada, doutora. Absolutamente nada.
```

**Classificação esperada:** HIGH_RISK — `humanReviewRequired: true`

---

## Cenário 3 — MONITORAR (sintomas moderados, ambivalência)
**Arquivo:** `scenario_03_monitoring_moderado.wav`
**Perfil:** Juliana, 26 anos, 5 semanas pós-parto, primeiro filho

**Tom de voz:** Alterna entre soar razoavelmente bem e momentos de angústia.
Fala um pouco mais rápida quando está ansiosa. Algumas pausas de reflexão.
Não tão pesada quanto os cenários 1 e 2.

**Texto para TTS:**
```
Olha doutora, tem dias bons e dias ruins, né. Ontem estava bem, consegui dar
banho nele, dar de mamar, até saí um pouco de casa.
[pausa 0.5s]
Mas aí de repente bate um choro à toa. Ontem mesmo fiquei chorando uns vinte
minutos sem motivo nenhum. Do nada. Não entendo o que acontece comigo.
[pausa 0.5s]
Estou muito cansada, isso sim. Ele mama muito à noite, não me deixa dormir.
Durmo em pedaços. Às vezes fico tão cansada que fico irritada com meu marido
sem motivo.
[pausa 0.5s]
Não acho que é grave não. Pelo menos é o que eu fico me dizendo.
Mas às vezes fico muito ansiosa quando preciso sair de casa com ele. Fico
com medo de algo acontecer com ele. Não consigo parar de me preocupar.
[pausa 0.5s]
Minha sogra fica falando que estou sendo dramática, que isso é normal.
Mas não sei, doutora. Não sei se é normal sentir isso tudo assim.
Meu apetite também tá meio estranho. Às vezes não como o dia todo, às vezes
como demais.
```

**Classificação esperada:** MONITORING — `humanReviewRequired: true` (se confidence < 0.75)

---

## Cenário 4 — MONITORAR (ansiedade pós-parto, risco leve-moderado)
**Arquivo:** `scenario_04_monitoring_ansiedade.wav`
**Perfil:** Fernanda, 35 anos, 8 semanas pós-parto, segundo filho

**Tom de voz:** Ansiosa, fala um pouco mais rápida que o normal. Preocupada.
Mas não completamente abatida — consegue articular bem os pensamentos.

**Texto para TTS:**
```
Doutora, eu fico tão ansiosa. Muito ansiosa mesmo.
Fico olhando ele dormir para ver se está respirando. Toda noite fico acordada
com medo. Coloco a mão no peito dele umas cinco, seis vezes por noite para
confirmar que ele está respirando.
[pausa 0.5s]
Meu marido fala que eu exagero, que isso não é normal. Mas eu não consigo
parar de pensar que algo pode dar errado. Qualquer barulhinho diferente e já
entro em pânico.
[pausa 0.5s]
De resto eu estou bem, acho. Estou conseguindo amamentar, ele engordou bem,
a pediatra está satisfeita com o desenvolvimento.
Mas esse negócio de não conseguir dormir mesmo quando ele dorme está me
desgastando muito. Fico exausta mas não consigo desligar a cabeça.
[pausa 0.5s]
Às vezes fico irritada sem motivo. Ontem gritei com meu marido por uma coisa
boba e depois fiquei me sentindo muito culpada. Não sou assim normalmente.
```

**Classificação esperada:** MONITORING — `humanReviewRequired: true/false` dependendo da confiança

---

## Cenário 5 — BAIXO RISCO (adaptação normal ao pós-parto)
**Arquivo:** `scenario_05_low_risk.wav`
**Perfil:** Beatriz, 30 anos, 4 semanas pós-parto, primeiro filho

**Tom de voz:** Mais energética, embora claramente cansada. Fala fluente,
com variação natural de entonação. Pode sorrir durante a fala.
Claramente conectada com o bebê.

**Texto para TTS:**
```
Oi doutora, estou bem! Cansada, é claro, né. Recém-nascido é muito trabalho,
todo mundo avisou mas é diferente quando você vive de verdade.
[pausa 0.5s]
Mas estou conseguindo me virar bem. A amamentação está indo ótimo, ela pega
bem, está engordando certinho. Tive uma mastite no começo que a senhora me
ajudou a tratar, graças a Deus passou rápido.
[pausa 0.5s]
Meu marido está de licença paternidade ainda, está ajudando muito. Fazemos
revezamento à noite, então consigo dormir em blocos razoáveis.
[pausa 0.5s]
Às vezes fico bem emotiva de repente, sabe? Tipo, ontem ela me olhou e deu
um sorrisinho, provavelmente foi gasinho mas eu chorei de alegria.
Fico emocionada por coisas pequenas assim. Mas são lágrimas de felicidade,
de gratidão.
[pausa 0.5s]
Estou comendo bem, me preocupo em manter a hidratação por causa do leite.
Me preocupo com coisas normais de mãe de primeira viagem, pergunto bastante
coisa no grupo de WhatsApp das mamães, mas nada que me tire o sono.
Estou bem, doutora. Cansada mas muito feliz.
```

**Classificação esperada:** LOW_RISK — `humanReviewRequired: false`

---

## Instruções para Geração no ElevenLabs

1. Acesse [elevenlabs.io](https://elevenlabs.io)
2. Selecione **Text to Speech**
3. Escolha voz feminina (ex: "Bella", "Rachel") — configure idioma para pt-BR se disponível
4. Cole o texto de cada cenário (sem as linhas `[pausa Xs]` — o ElevenLabs detecta pausas por vírgulas e reticências)
5. Para pausas explícitas, use `<break time="2s"/>` se a plataforma suportar SSML
6. Exporte como **WAV 44.1kHz** e converta para 16kHz mono com:
   ```bash
   ffmpeg -i input.wav -ar 16000 -ac 1 scenario_01_high_risk_ideacao.wav
   ```

## Instruções para Azure TTS (via Azure Portal ou SDK)

```python
import azure.cognitiveservices.speech as speechsdk

speech_config = speechsdk.SpeechConfig(subscription="KEY", region="brazilsouth")
speech_config.speech_synthesis_voice_name = "pt-BR-FranciscaNeural"

# Para ritmo mais lento (cenários 1 e 2), use SSML:
ssml = """
<speak version='1.0' xml:lang='pt-BR'>
  <voice name='pt-BR-FranciscaNeural'>
    <prosody rate='slow' pitch='-5%'>
      Doutora, eu não sei mais o que fazer...
    </prosody>
  </voice>
</speak>
"""
```
