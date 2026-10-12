"""Gera várias árvores (alturas e grossuras variadas) com folhas em cartões, sem faces invertidas.
Uso: blender -b -P gen_trees.py -- [qtd=8] [seed=1] [pasta_fbx]
Unidade: 1 unidade Blender = 1 stud. Origem de cada árvore = base do tronco.
Atlas esperado: metade esquerda (u 0-0.5) = casca, metade direita (u 0.5-1) = folha RGBA.
"""
import math
import random
import sys

import bmesh
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
COUNT = int(args[0]) if len(args) > 0 else 8
SEED = int(args[1]) if len(args) > 1 else 1
OUT = args[2] if len(args) > 2 else None

HEIGHTS = [5, 8, 12, 16, 22]                       # studs
THICK = {"fino": 0.02, "medio": 0.035, "grosso": 0.06}  # raio_base / altura
SEG = 8                                            # lados do tronco
BARK = (0.0, 0.0, 0.5, 1.0)                        # u0, v0, u1, v1
LEAF = (0.5, 0.0, 1.0, 1.0)
MAX_TRIS = 1500


def tube(bm, p, d, r1, r2, length):
    """Tronco/galho aberto com costura duplicada (UV sem esticar). Normais para fora."""
    rot = d.to_track_quat("Z", "Y").to_matrix()
    rings = []
    for z, r in ((0, r1), (length, r2)):
        rings.append([bm.verts.new(p + rot @ Vector((r * math.cos(a), r * math.sin(a), z)))
                      for a in (2 * math.pi * i / SEG for i in range(SEG + 1))])
    uv = bm.loops.layers.uv.verify()
    for i in range(SEG):
        f = bm.faces.new((rings[0][i], rings[0][i + 1], rings[1][i + 1], rings[1][i]))
        for loop, (u, v) in zip(f.loops, ((i, 0), (i + 1, 0), (i + 1, 1), (i, 1))):
            loop[uv].uv = (BARK[0] + (BARK[2] - BARK[0]) * u / SEG,
                           BARK[1] + (BARK[3] - BARK[1]) * v)


def card(bm, c, size, rng):
    """Cartão de folha em orientação aleatória + cópia invertida afastada 3 mm (dupla face sem z-fighting)."""
    n = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1) + 0.6)).normalized()
    u = n.orthogonal().normalized() * size / 2
    v = n.cross(u).normalized() * size / 2
    uv = bm.loops.layers.uv.verify()
    quad = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    for flip in (1, -1):
        off = n * 0.003 * (flip == -1)
        pts = [bm.verts.new(c + off + u * a + v * b) for a, b in quad][::flip]
        f = bm.faces.new(pts)
        for loop, (a, b) in zip(f.loops, [q for q in quad][::flip]):
            loop[uv].uv = (LEAF[0] + (LEAF[2] - LEAF[0]) * (a + 1) / 2,
                           LEAF[1] + (LEAF[3] - LEAF[1]) * (b + 1) / 2)


def make_tree(name, height, ratio, rng):
    bm = bmesh.new()
    r0 = height * ratio
    d = Vector((rng.uniform(-.08, .08), rng.uniform(-.08, .08), 1)).normalized()
    L = height * 0.75
    tube(bm, Vector(), d, r0, r0 * 0.35, L)
    top = d * L
    leaf = max(1.2, height * 0.18)
    tips = [top]
    for _ in range(3 + int(height // 5)):
        t = rng.uniform(0.45, 0.9)
        a, tilt = rng.uniform(0, 2 * math.pi), math.radians(rng.uniform(35, 70))
        bd = Vector((math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt)))
        bl = height * rng.uniform(0.18, 0.32) * (1.15 - t * 0.5)
        start = d * (L * t)
        rb = (r0 + (r0 * 0.35 - r0) * t) * 0.5
        tube(bm, start, bd, rb, rb * 0.3, bl)
        tips.append(start + bd * bl)
    center = sum(tips, Vector()) / len(tips)
    for tip in tips:
        for _ in range(4):
            card(bm, tip + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-.3, 1))) * leaf * .5,
                 leaf * rng.uniform(.8, 1.2), rng)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    tris = 2 * len(bm.faces)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    # Normais da copa apontando para fora do centro: folhas sem "manchas" escuras (Blender 4.1+; antes exige auto-smooth).
    try:
        if hasattr(me, "use_auto_smooth"):
            me.use_auto_smooth = True
        me.normals_split_custom_set_from_vertices(
            [(v.co - center).normalized() if v.co.z > L * 0.4 else v.normal for v in me.vertices])
    except (AttributeError, RuntimeError):
        pass  # sem normais custom: aplique Data Transfer/Normal Edit manualmente (ver SKILL.md)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob, tris


def main():
    rng = random.Random(SEED)
    combos = [(h, k) for h in HEIGHTS for k in THICK]
    rng.shuffle(combos)
    for i in range(COUNT):
        h, k = combos[i % len(combos)]
        name = f"Arvore_H{h}_{k}_{i:02d}"
        ob, tris = make_tree(name, h * rng.uniform(.9, 1.1), THICK[k], rng)
        print(f"{name}: {tris} tris" + ("  <-- ACIMA DO ORÇAMENTO" if tris > MAX_TRIS else ""))
        if OUT:
            bpy.ops.object.select_all(action="DESELECT")
            ob.select_set(True)
            bpy.ops.export_scene.fbx(filepath=f"{OUT}/{name}.fbx", use_selection=True)
        ob.location = (i * 14, 0, 0)  # só para visualizar em fileira


main()
