"""Blend two measured profiles into one target: tone from A, colour pulled toward B.

Used to build a look that keeps a reference's tonality while borrowing another's
cast at a chosen strength - "Marvel, but a bit greener" - without hand-authoring
numbers that no reference supports.

Usage: blend_profile.py <tone.json> <colour.json> <out_label>
  env: MIX (0-1 toward the colour source), SAT_MIX (scale on saturation)
"""
import json, os, sys

A = json.load(open(sys.argv[1]))
B = json.load(open(sys.argv[2]))
LABEL = sys.argv[3]
MIX = float(os.environ.get("MIX", 0.45))
# Weighting R and B apart is what separates olive (blue pulled down harder than
# red) from a flat green-grey.
MIX_RG = float(os.environ.get("MIX_RG", MIX))
MIX_BG = float(os.environ.get("MIX_BG", MIX))
SAT_MIX = float(os.environ.get("SAT_MIX", 0.88))

bb = {round(b["luma"], 3): b for b in B["bins"]}
keys = sorted(bb)


def at(lu, field):
    if lu <= keys[0]:
        return bb[keys[0]][field]
    if lu >= keys[-1]:
        return bb[keys[-1]][field]
    for i in range(len(keys) - 1):
        if keys[i] <= lu <= keys[i + 1]:
            f = (lu - keys[i]) / (keys[i + 1] - keys[i])
            return bb[keys[i]][field] + (bb[keys[i + 1]][field] - bb[keys[i]][field]) * f
    return bb[keys[-1]][field]


out = {"label": LABEL, "tone_from": A["label"], "colour_from": B["label"],
       "mix_rg": MIX_RG, "mix_bg": MIX_BG, "sat_mix": SAT_MIX,
       "luma": A["luma"], "mean": A["mean"], "bins": []}
for bin_a in A["bins"]:
    lu = bin_a["luma"]
    out["bins"].append({
        "luma": lu, "share": bin_a["share"],
        "r_g": round(bin_a["r_g"] + (at(lu, "r_g") - bin_a["r_g"]) * MIX_RG, 4),
        "b_g": round(bin_a["b_g"] + (at(lu, "b_g") - bin_a["b_g"]) * MIX_BG, 4),
        "sat": round(bin_a["sat"] * SAT_MIX, 4),
    })

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"profile_{LABEL}.json")
json.dump(out, open(p, "w"), indent=1)
print(f"wrote {p}   tone={A['label']}  colour->{B['label']} "
      f"rg@{MIX_RG} bg@{MIX_BG}  sat x{SAT_MIX}")
print(f"{'luma':>6}{'R-G A':>9}{'R-G mix':>9}{'B-G A':>9}{'B-G mix':>9}")
for a, o in zip(A["bins"], out["bins"]):
    if 0.09 <= o["luma"] <= 0.85:
        print(f"{o['luma']:6.3f}{a['r_g']:+9.4f}{o['r_g']:+9.4f}{a['b_g']:+9.4f}{o['b_g']:+9.4f}")
