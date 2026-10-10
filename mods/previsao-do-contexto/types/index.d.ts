export type Leitura = { tokens: number; janela: number }

declare module 'claude-code' {
  interface PluginState {
    'previsao-do-contexto': { leituras: Leitura[] }
  }
}
