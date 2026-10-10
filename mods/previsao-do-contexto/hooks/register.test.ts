import { test, expect } from 'claude-code/testing'
import { tempo, k, barra } from './register'

test('faixas do tempo', () => {
  expect([0, 24, 25, 49, 50, 74, 75, 89, 90, 100].map(p => tempo(p).palavra)).toEqual([
    'Limpo', 'Limpo', 'Nublado', 'Nublado', 'Chuva', 'Chuva', 'Tempestade', 'Tempestade', 'Compacta logo', 'Compacta logo',
  ])
})

test('formato e barras', () => {
  expect(k(134000)).toBe('134k')
  expect(barra({ tokens: 200, janela: 200 })).toBe('█')
  expect(barra({ tokens: 0, janela: 200 })).toBe('▁')
})
