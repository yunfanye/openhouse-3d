"""Common-area broadleaf trees with an explicit crown envelope (imported by context.py only).

archviz.trees.oak grows coast-live-oak forms whose leaf clumps sit at the twig ends; the honey locusts, maples, ash
and birches round the pond (photos 26, 29, 31, 32) need other silhouettes: a dense dome on a short trunk (26's big
locust), low-forking multi-stem trees whose crowns meet over the path (29), narrow young trees on the far bank (31)
and open birch clumps.  Here the crown is an ellipsoid envelope (width w, crown base hb .. top h, a flatter
underside); limbs grow from the fork(s) toward points inside the envelope, branches toward the shell, and leaf
clusters (archviz.trees.Tree.clump with no dark core) sit round the branch tips plus fill clusters on the shell.
Gaps are carved with 3-D noise so the sky shows through (the listing photos' crowns are airy).  Sizes are the
targets measured in the photos (REFERENCES.md)."""
import math
from mathutils import Vector, noise
from archviz import trees as _tr

FORMS = {
    # crown base (fraction of h), underside flattening, shell bias, gap threshold, limb rise
    'dome':      dict(hb=0.12, under=0.62, gap=-0.62, rise=(0.35, 0.9)),
    'round':     dict(hb=0.30, under=0.70, gap=-0.25, rise=(0.5, 1.1)),
    'oval':      dict(hb=0.30, under=0.75, gap=-0.25, rise=(0.8, 1.6)),
    'multistem': dict(hb=0.16, under=0.70, gap=-0.42, rise=(0.3, 0.8)),
    'column':    dict(hb=0.10, under=0.90, gap=-0.40, rise=(2.2, 3.5)),
    'open':      dict(hb=0.38, under=0.70, gap=0.05, rise=(0.9, 1.9)),
}


def broadleaf(name, base, h, w, seed, mats, detail=1.0, form='dome', stems=1, fork=0.25, trunk_r=None, lean=0.0, card=None,
              cov=0.7, coll='Landscape'):
    """mats may carry 'core': then every leaf cluster gets an opaque inner blob (low-detail / instanced trees: stops
    rays after a few alpha cards - Cycles returns black past transparent_max_bounces)."""
    """One tree at base (x, y, z): total height h, crown width w.  stems > 1: a clump of leaning stems from the
    ground (fork = fraction of h where each stem divides).  mats: {'bark', 'leaf'}."""
    F = FORMS[form]
    T = _tr.Tree(seed, detail)
    rng = T.rng
    bx, by, bz = base
    hb = F['hb'] * h
    rx = w / 2.0
    rz_up = (h - hb) * 0.5
    cz = bz + hb + rz_up * (1.0 - 0.0)            # envelope centre height
    cz = bz + hb + (h - hb) * (F['under'] / (1.0 + F['under']))
    rz_up = bz + h - cz
    rz_dn = cz - (bz + hb)
    C = Vector((bx, by, cz))
    ph = Vector((rng.uniform(0, 100), rng.uniform(0, 100), rng.uniform(0, 100)))
    tr = trunk_r or max(0.05, h * (0.018 if stems == 1 else 0.012))

    def env(d, u):
        """Point in the envelope: direction d (unit), fraction u of the radius."""
        rz = rz_up if d.z >= 0 else rz_dn
        return Vector((bx + d.x * rx * u, by + d.y * rx * u, cz + d.z * rz * u))

    def rand_dir(up=0.2):
        while True:
            v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
            if 0.05 < v.length <= 1.0:
                v.normalize()
                v.z += up
                return v.normalized()

    # ---- stems and limbs
    tips = []
    for k in range(stems):
        a = 2 * math.pi * k / stems + rng.uniform(-0.5, 0.5)
        tilt = (lean if stems == 1 else rng.uniform(0.10, 0.22))
        d0 = Vector((math.cos(a) * tilt, math.sin(a) * tilt, 1.0)).normalized()
        p0 = Vector((bx + (0.12 * math.cos(a) if stems > 1 else 0.0), by + (0.12 * math.sin(a) if stems > 1 else 0.0), bz - 0.3))
        hf = h * fork * rng.uniform(0.85, 1.15)
        pts, radii, dend = T.curve(p0, d0, hf / max(0.3, d0.z) + 0.3, tr, tr * 0.8, n_sub=3, wiggle=0.05)
        T.tube(pts, radii)
        top = pts[-1]
        nl = rng.randint(3, 4) if stems > 1 else rng.randint(4, 6)
        for i in range(nl):
            az = 2 * math.pi * i / nl + rng.uniform(-0.4, 0.4) + a
            rise = rng.uniform(*F['rise'])
            dd = Vector((math.cos(az), math.sin(az), rise)).normalized()
            # aim at a point inside the envelope along that direction
            tgt = env(Vector((dd.x, dd.y, max(-0.2, dd.z - 0.3))).normalized(), rng.uniform(0.45, 0.7))
            L = (tgt - top).length
            lp, lr, ld = T.curve(top, (tgt - top).normalized(), L, tr * 0.6, tr * 0.22, n_sub=3, wiggle=0.08, tropism=0.03)
            T.tube(lp, lr)
            nb = rng.randint(2, 4)
            for j in range(nb):
                t = rng.uniform(0.5, 1.0) if j < nb - 1 else 1.0
                q, dq, rq = T._at(lp, lr, t)
                sd = (dd + rand_dir(0.3) * 0.8).normalized()
                end = env(sd, rng.uniform(0.82, 0.97))
                Lb = (end - q).length
                if Lb < 0.3:
                    continue
                bp, br, _ = T.curve(q, (end - q).normalized(), Lb, max(0.012, rq * 0.6), 0.008, n_sub=2, wiggle=0.12, gravity=0.04)
                if detail >= 0.3:
                    T.tube(bp, br)
                tips.append(bp[-1])
    # ---- leaf clusters: round the branch tips + fill clusters on the shell
    card = card or ((0.17 if detail >= 0.9 else 0.30) * (w / 8.0) ** 0.35)     # finer sprays on trees seen from < 25 m
    rc = max(0.4, (0.055 if form in ('dome', 'multistem') else 0.085) * w)      # fine clusters on the dense crowns
    area = 4 * math.pi * ((rx * rx + rx * (rz_up + rz_dn) / 2 + rx * (rz_up + rz_dn) / 2) / 3.0)
    n_fill = int(area / (rc * rc * 2.2))
    centres = [(t, rc * rng.uniform(0.8, 1.15)) for t in tips]
    for _ in range(n_fill):
        d = rand_dir(0.15)
        centres.append((env(d, 1.0 - 0.3 * rng.random() ** 1.5), rc * rng.uniform(0.75, 1.2)))
    for (c, r) in centres:
        n = noise.noise((c - C) * (1.6 / max(1.0, w / 6.0)) + ph)
        if n < F['gap']:
            continue
        T.clump(c, r, card, cov=cov, up_bias=0.25, flat=0.2, shell=0.9, core=0.55 if mats.get('core') else 0.0, cap=1200)
    T.build(name, mats['bark'], mats['leaf'], coll=coll, core_mat=mats.get('core'), core_seg=6)
    return T
