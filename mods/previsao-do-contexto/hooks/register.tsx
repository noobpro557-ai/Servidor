import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { Leitura } from '../types'

const leituras = atom({ plugin: 'previsao-do-contexto', key: 'leituras' } as const, [] as Leitura[])

const BARRAS = '▁▂▃▄▅▆▇█'
const TURNOS = 12

// ASCII puro nos símbolos: alinham em qualquer fonte do terminal do VS Code.
export const tempo = (pct: number) =>
  pct < 25 ? { simbolo: '*', palavra: 'Limpo', cor: 'yellow' }
  : pct < 50 ? { simbolo: '~', palavra: 'Nublado', cor: 'cyan' }
  : pct < 75 ? { simbolo: '/', palavra: 'Chuva', cor: 'blue' }
  : pct < 90 ? { simbolo: '!', palavra: 'Tempestade', cor: 'magenta' }
  : { simbolo: '!!', palavra: 'Compacta logo', cor: 'red' }

export const k = (n: number) => (n >= 1000 ? `${Math.round(n / 1000)}k` : `${n}`)

export const barra = (l: Leitura) =>
  BARRAS[Math.min(7, Math.floor((l.tokens / l.janela) * 8))]

export const register: Register = on => {
  on('turn.complete', async ($, e, next) => {
    const { context } = await $.session.usage()
    if (context.tokens !== undefined && context.window > 0) {
      const nova: Leitura = { tokens: context.tokens, janela: context.window }
      await update($, leituras, l => [...l, nova].slice(-TURNOS))
    }
    return next(e)
  })

  // Um /clear zera a janela: recomeça o histórico.
  on('session.end', async ($, e, next) => {
    if (e.reason === 'clear') await update($, leituras, () => [])
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const hist = await read($, leituras)
    const atual = hist[hist.length - 1]
    if (e.props.hasSurvey || !atual) return next(e)

    const { Box, Text } = $.ui.resolve(e)
    const pct = Math.round((atual.tokens / atual.janela) * 100)
    const t = tempo(pct)
    const antes = hist.length > 1 ? hist[hist.length - 2].tokens : 0
    const delta = atual.tokens - antes

    return (
      <Box>
        <Text color={t.cor} bold>{t.simbolo} {t.palavra}</Text>
        <Text> {pct}% · {k(atual.tokens)} / {k(atual.janela)} · </Text>
        <Text color={t.cor}>{hist.map(barra).join('')}</Text>
        <Text dimColor> · {delta >= 0 ? '+' : '-'}{k(Math.abs(delta))} no último turno</Text>
      </Box>
    )
  })
}
