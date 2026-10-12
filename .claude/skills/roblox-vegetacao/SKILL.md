---
name: roblox-vegetacao
description: Ajuda a criar vegetação (árvores, arbustos, grama, flores, samambaias) detalhada para jogos Roblox usando Blender e Unreal Engine, e audita se o modelo está pesado/exagerado para o Roblox. Use quando o usuário falar de Roblox, vegetação, árvore, planta, folhagem, MeshPart, LOD, orçamento de triângulos ou exportar do Blender/Unreal para o Roblox.
---

# Vegetação para Roblox (Blender / Unreal)

Objetivo: vegetação **completa e rica em detalhe visual**, dentro de um orçamento que roda em celular. Detalhe vem de **textura + cartões com recorte (alpha)**, não de triângulos.

## Fluxo

1. **Briefing** (pergunte só o que faltar): espécie/estilo (realista, low-poly, estilizado), plataforma-alvo (mobile é o limite), tamanho em studs, quantas instâncias aparecem juntas na tela.
2. **Escolher o tipo** na tabela de orçamento abaixo.
3. **Modelar** (Blender é a fonte; Unreal só para referência/bake — Nanite, Lumen e foliage do Unreal **não** existem no Roblox).
4. **Exportar** e **auditar** com o checklist e `check_budget.py`.
5. **Reportar** veredito: OK / Pesado / Exagerado, com o que cortar.

## Orçamento por tipo (alvo, não regra oficial)

| Tipo | Triângulos LOD0 | Textura | Observação |
|---|---|---|---|
| Grama (tufo) | 20–80 | 512 | cartões cruzados, muitas instâncias |
| Flor / arbusto pequeno | 80–300 | 512–1024 | |
| Arbusto grande / samambaia | 300–800 | 1024 | |
| Árvore de fundo | 300–1000 | 1024 | |
| Árvore principal (herói) | 1500–4000 | 2048 | só poucas na cena |

Limites duros do Roblox: **21.844 triângulos por MeshPart**, textura até 4096. Chegar perto disso para uma planta já é **exagero**.

## Técnicas que dão detalhe sem peso

- **Cartões de folhas**: planos com textura RGBA de galhos/folhas (atlas), em vez de modelar cada folha. No Roblox: `SurfaceAppearance` com `AlphaMode = Transparency` (ou recorte) — evite `Transparency` parcial em massa (overdraw).
- **Tronco** com 6–10 lados, normal map para casca; ramos grossos em geometria, finos em cartão.
- **Vertex color / AO bakeado** para sombra interna da copa (barato, muda muito o visual).
- **Variação**: 3–5 variações de malha + rotação/escala aleatória, em vez de 1 malha ultra detalhada.
- **Mesmo MeshId reutilizado** → o Roblox instancia; não duplique malhas únicas.
- **LODs**: gere LOD1 (~50%) e LOD2 (~20%) ou um billboard no fim; no Studio use `RenderFidelity`/LOD automático do MeshPart.
- **Atlas único** por conjunto de plantas (1 material = menos draw calls).
- **Pivô** na base do tronco, Z-up no Blender, escala: 1 stud ≈ 0,28 m (personagem ≈ 5 studs).

## Blender (passos)

1. Árvore: Curve/Skin modifier ou addon (Sapling Tree Gen) → Decimate/limpar → converter para mesh.
2. Folhagem: planos com UV no atlas; Weight Normals/“normais para cima” na copa (shading suave de volume).
3. Bake: AO, normal, base color → atlas.
4. Aplicar escalas (Ctrl+A), origem na base, nomear `Arvore_Carvalho_LOD0`.
5. Exportar FBX (ou glTF) com `Apply Transform`, só a malha; importar pelo Asset Manager / 3D Importer do Studio.

## Unreal (quando usar)

Use para **look-dev e referência** (ex.: Megascans/Quixel) e para bake de texturas/atlas de folhagem. Reduza para o orçamento acima antes de exportar. Nanite e vento por World Position Offset não existem no Roblox: deixe a planta estática ou use um balanço leve por script (TweenService) só nas plantas próximas.

## Checklist “está exagerado?”

- [ ] Triângulos ≤ alvo da tabela (LOD0)?
- [ ] Soma da cena: ~100 árvores × tris cabe? (estimativa: instâncias visíveis × tris ≲ 300k em mobile)
- [ ] Texturas ≤ 2048 (1024 para a maioria)? Sem textura 4096 em planta pequena?
- [ ] Um atlas/material por conjunto?
- [ ] Alpha só onde precisa; poucos planos sobrepostos?
- [ ] LOD ou billboard para distância?
- [ ] Sem geometria interna oculta / faces duplicadas / n-gons?
- [ ] Colisão: `CanCollide=false` em folhagem; `CollisionFidelity=Box` no tronco.
- [ ] Escala em studs coerente e pivô na base?

## Veredito (formato da resposta)

```
Modelo: <nome>   Tris: N (alvo M)   Textura: WxH   Materiais: K
Veredito: OK | PESADO | EXAGERADO
Cortar: <ações concretas, em ordem de ganho>
```

Regra: > 2× o alvo = EXAGERADO; 1–2× = PESADO; ≤ alvo = OK. Se for exagerado, proponha antes de refazer: decimar, trocar geometria por cartão+alpha, baixar textura, adicionar LOD.

## Script de auditoria

`check_budget.py` (nesta pasta) roda no Blender (`blender -b arquivo.blend -P check_budget.py -- grama|arbusto|arvore|heroi`) e imprime tris, texturas e veredito para os objetos de malha da cena.
