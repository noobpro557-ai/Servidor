---
name: roblox-arvores-vfx
description: Gera vários modelos de árvore no Blender (troncos finos/grossos, alturas diferentes, folhas sem bugs de normal/z-fighting/alpha) para Roblox, e ajuda a criar e ajustar efeitos VFX (folhas caindo, vaga-lumes, pólen, raios de luz, lascas de madeira) com ParticleEmitter, Beam e Trail. Use quando o usuário pedir várias árvores, variações de árvore, folhas bugadas/escuras/piscando, ou VFX/partículas/efeitos para Roblox.
---

# Árvores em lote + VFX para Roblox

Complementa `roblox-vegetacao` (orçamento de triângulos e veredito). Reuse a tabela de lá; aqui o foco é **gerar variações** e **não bugar folhas**.

## Parte 1 — Gerar várias árvores

Rode `gen_trees.py` (nesta pasta):

```
blender -b -P gen_trees.py -- 10 42 /caminho/saida_fbx
#                             qtd seed pasta (opcional: exporta 1 FBX por árvore, na origem)
```

- Combina **alturas** (5, 8, 12, 16, 22 studs, ±10%) × **grossuras** (`fino` 2%, `medio` 3,5%, `grosso` 6% da altura) e sorteia inclinação, nº e ângulo de galhos.
- Tronco e galhos são tubos de 8 lados com costura duplicada (UV sem esticar); folhas são **cartões** em atlas, não folhas modeladas.
- Imprime triângulos por árvore e avisa acima de 1500. Ajuste `HEIGHTS`, `THICK`, `MAX_TRIS` no topo do script.
- Para uma família específica (ex.: só pinheiros finos e altos), edite essas listas e mude cartões por galho (`range(4)`) e ângulo `tilt`.
- Atlas esperado: **esquerda = casca, direita = folha RGBA** (um material só = menos draw calls).

> O script não foi executado aqui (Blender não está instalado no ambiente). Rode com 2–3 árvores primeiro e confira no viewport antes de gerar lote.

## Por que as folhas ficam “bugadas” e como o script evita

| Sintoma | Causa | Correção |
|---|---|---|
| Folha invisível de um lado | Roblox não renderiza face de trás | cópia invertida de cada cartão (feito no script) |
| Folhas piscando/serrilhadas | z-fighting entre cartão e cópia coplanares | cópia afastada 3 mm ao longo da normal (feito) |
| Folhas escuras/manchadas | normais por cartão apontam em direções aleatórias | normais da copa apontando do centro para fora (feito, Blender 4.1+; antes ative Auto Smooth). Manual: modificador **Data Transfer → Custom Normals** com uma esfera, ou **Normal Edit → Directional** |
| Face azul/vermelha | face invertida | Viewport Overlays → **Face Orientation**: tudo azul; se não, Mesh → Normals → Recalculate Outside |
| Halo branco/preto na borda | alpha com cor de fundo | preencher pixels transparentes com a cor da folha (dilatar bordas) antes de exportar |
| Folha “some” ao longe | mipmap mistura alpha | padding de 4–8 px entre folhas no atlas; evite folhas finas demais |
| Troncos esticados | UV sem costura / escala não aplicada | UV por anel (feito); `Ctrl+A → Scale` antes de exportar |
| Pesado | muitos cartões | menos cartões maiores > muitos pequenos; cheque orçamento |

No Roblox: `SurfaceAppearance.AlphaMode = Transparency`; evite muitas camadas translúcidas sobrepostas (ordenação ruim e overdraw). Colisão: `CanCollide = false` na folhagem, `CollisionFidelity = Box` no tronco.

## Checklist antes de aprovar um lote

- [ ] Face Orientation toda azul, sem faces soltas
- [ ] Origem na base, escala aplicada, 1 unidade = 1 stud
- [ ] Triângulos dentro do alvo (veja `roblox-vegetacao`)
- [ ] Olhar pelo menos 3 ângulos: contra a luz, de cima, de longe (as folhas não podem sumir nem brilhar demais)
- [ ] Variação visível entre as árvores do lote (altura, grossura, silhueta)

---

## Parte 2 — VFX no Roblox

Princípio: **poucas partículas, bem texturizadas**. Cada emitter ≈ `Rate × Lifetime` partículas vivas; mire em **≤ 50 por emitter** e **poucas centenas na cena** (mobile é o teto). Efeito bom = textura boa + curvas (`NumberSequence`/`ColorSequence`), não quantidade.

### Receitas (ParticleEmitter, valores iniciais)

| Efeito | Texture | Rate / Lifetime | Movimento | Detalhes |
|---|---|---|---|---|
| Folhas caindo | folha (do atlas ou sprite) | 3 / 6–9 | Speed 1–2, `Acceleration=(0,-1.5,0)`, `Drag=1`, SpreadAngle 180 | `RotSpeed` ±90, `Rotation` 0–360, Size 0,5–1; Transparency 0→0 e sobe a 1 no fim |
| Pólen / poeira de luz | círculo suave | 4 / 5–8 | Speed 0,2–0,5, `Acceleration=(0,.1,0)` | `LightEmission=1`, `LightInfluence=0`, Size 0,1–0,3, cor quente |
| Vaga-lumes | círculo suave | 1,5 / 4–6 | Speed 0,5, SpreadAngle 180 | `LightEmission=1`, Size pulsando (NumberSequence 0→0,3→0), amarelo-esverdeado; `PointLight` fraco no pai |
| Raios de luz entre árvores | — | — | — | `Atmosphere` + `SunRaysEffect` (Intensity baixo) + `ColorCorrection`; sem partículas |
| Lascas ao cortar | lasca/quadrado | `Emit(8–12)` por golpe | Speed 8–15, `Acceleration=(0,-40,0)`, Lifetime 0,4–0,8 | dispare com `:Emit()`, `Enabled=false` |
| Folhas no vento | folha | 6 / 3–5 | Speed 6–10 na direção do vento, SpreadAngle 20 | gire `RotSpeed`; `Drag` baixo |
| Rastro de folha / magia | — | — | — | `Trail` (Lifetime 0,3–0,6, `LightEmission`, transparência 0→1) |

Sprite sheet animado: gere os frames no Blender (render) ou Unreal/Niagara (só como ferramenta de render — Niagara não importa no Roblox) e use `FlipbookLayout` (Grid 2x2/4x4/8x8) + `FlipbookMode`.

### Ajuste (um parâmetro por vez)

| Se parece… | Mexa em |
|---|---|
| plástico/chapado | textura com gradiente suave; `Transparency` com fade-in/out; variar `Size` (NumberSequence com `Envelope`/ruído) |
| “nuvem de pontos” | cair `Rate`, subir `Size`, adicionar `Rotation`/`RotSpeed` |
| duro, aparece/some de repente | NumberSequence de Transparency 1→0→0→1 |
| muito brilhante/estourado | `LightEmission` ↓, `LightInfluence` ↑, ou `Bloom` fraco |
| artificial/linear | `Acceleration` + `Drag`; ruído com `SpreadAngle` e `Speed` como range |
| lag | `Rate` ↓, `Lifetime` ↓, `Enabled=false` quando longe (checar distância por script a cada ~0,5 s), `LockedToPart` só se precisar |

Vento global (se disponível na sua versão): `Workspace.GlobalWind` com `WindAffectsDrag` nos emitters para folhas obedecerem ao vento.

### Fluxo ao pedir um efeito

1. Pergunte: o quê, onde, intensidade, mobile? (só o que faltar)
2. Entregue o **código Luau** que cria o emitter (propriedades da receita) ou o passo a passo no Studio, mais a **textura** a gerar (tamanho 256–512, fundo transparente).
3. Revise com a tabela “Ajuste” e o orçamento de partículas; diga se está exagerado e o que cortar.
