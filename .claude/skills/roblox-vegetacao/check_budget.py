"""Audita orçamento de vegetação p/ Roblox. Uso:
blender -b arquivo.blend -P check_budget.py -- arvore
"""
import sys
import bpy

# tipo: (tris alvo LOD0, textura máx em px)
BUDGET = {
    "grama": (80, 512),
    "arbusto": (800, 1024),
    "arvore": (1000, 1024),
    "heroi": (4000, 2048),
}
ROBLOX_MAX_TRIS = 21844

kind = (sys.argv[sys.argv.index("--") + 1:] or ["arvore"])[0]
tris_max, tex_max = BUDGET[kind]

total = 0
for o in bpy.context.scene.objects:
    if o.type != "MESH":
        continue
    dg = bpy.context.evaluated_depsgraph_get()
    me = o.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    total += n
    flag = " > LIMITE ROBLOX" if n > ROBLOX_MAX_TRIS else ""
    print(f"{o.name}: {n} tris{flag}")

bad_tex = [i.name for i in bpy.data.images if max(i.size) > tex_max]
ratio = total / tris_max
verdict = "OK" if ratio <= 1 else "PESADO" if ratio <= 2 else "EXAGERADO"
print(f"TOTAL {total} tris (alvo {tris_max}) -> {verdict}")
if bad_tex:
    print(f"Texturas acima de {tex_max}px: {', '.join(bad_tex)}")
