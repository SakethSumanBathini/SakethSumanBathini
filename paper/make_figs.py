# Draws the paper's charts from the result files in ../results. Run from anywhere: python3 paper/make_figs.py
import json, math, importlib.util
import numpy as np
import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt
from matplotlib import font_manager

import os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'figs')
RES = os.path.join(HERE, '..', 'results')
# validated categorical slots (dataviz reference palette, light mode)
C1, C2, C3, C4 = '#2a78d6', '#eb6834', '#1baf7a', '#eda100'
INK, INK2, MUTED, GRID, BASE = '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#c3c2b7'
plt.rcParams.update({
    'font.family': 'Inter', 'font.size': 8.5, 'axes.titlesize': 9, 'axes.labelsize': 8.5,
    'axes.edgecolor': BASE, 'axes.linewidth': 0.8, 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2,
    'xtick.major.size': 0, 'ytick.major.size': 0, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False, 'legend.frameon': False,
    'pdf.fonttype': 3, 'lines.linewidth': 1.6, 'lines.markersize': 4,
})

def mark(ax, x, y, color, lead=False):
    ax.plot(x, y, color=color, lw=2.2 if lead else 1.5, marker='o', ms=4.2 if lead else 3.4,
            markeredgecolor='white', markeredgewidth=1.0, solid_capstyle='round', zorder=3 if lead else 2)

# ------------------------------------------------------------------ Fig: naming rate by channel
d = json.load(open(f'{RES}/sim_results.json'))['results']
def series(mode, V, key='correct'):
    rows = sorted([r for r in d if r['mode'] == mode and r['V'] == V], key=lambda r: r['k'])
    return [r['k'] for r in rows], [100 * r[key] for r in rows]
fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.85), sharey=True)
ax = axes[0]
spec = [('numbered', 4, 'Numbered, wording variants', C1, True), ('mcq', 1, 'MCQs, option order', C2, False),
        ('unnumbered', 4, 'No numbers, wording variants', C3, False), ('numbered', 1, 'Numbered, order only', C4, False)]
for mode, V, lab, col, lead in spec:
    x, y = series(mode, V); mark(ax, x, y, col, lead)
ax.set_title('Named at 10,000 : 1', loc='left', color=INK, fontweight='semibold')
ax.set_xlabel('Questions in the leak'); ax.set_ylabel('Share of leaks (%)')
ax.set_xticks(range(2, 11)); ax.set_ylim(-3, 103); ax.set_yticks([0, 25, 50, 75, 100])
ax = axes[1]
for mode, V, lab, col, lead in spec:
    x, y = series(mode, V, 'source_in_top5'); mark(ax, x, y, col, lead)
ax.set_title('Real source in the top-5 shortlist', loc='left', color=INK, fontweight='semibold')
ax.set_xlabel('Questions in the leak'); ax.set_xticks(range(2, 11))
handles = [plt.Line2D([], [], color=c, lw=2.2 if l else 1.5, marker='o', ms=4, markeredgecolor='white') for _, _, _, c, l in spec]
fig.legend(handles, [s[2] for s in spec], loc='lower center', ncol=2, bbox_to_anchor=(0.5, -0.02), fontsize=7.8, handlelength=1.8, columnspacing=2.4)
fig.tight_layout(rect=(0, 0.13, 1, 1)); fig.savefig(f'{OUT}/channels.pdf'); plt.close(fig)

# ------------------------------------------------------------------ Fig: tier 3
t3 = json.load(open(f'{RES}/tier3_results.json'))
fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.55), sharey=True)
ax = axes[0]
for delta, col, lab, lead in ((0.0, C1, 'No wrong answers', True), (0.1, C2, '1 wrong in 10', False), (0.2, C3, '1 wrong in 5', False)):
    rows = sorted([r for r in t3['answer_keys'] if r['code'] == 'code' and r['delta'] == delta], key=lambda r: r['k'])
    mark(ax, [r['k'] for r in rows], [100 * r['named'] for r in rows], col, lead)
    ax.annotate(lab, (rows[-1]['k'], 100 * rows[-1]['named']), xytext=(4, 0), textcoords='offset points', va='center', fontsize=7.5, color=INK2)
ax.set_title('Answer keys, 20 MCQs', loc='left', color=INK, fontweight='semibold')
ax.set_xlabel('Answers in the leaked key'); ax.set_ylabel('Named at 10,000 : 1 (%)')
ax.set_xticks(range(4, 21, 2)); ax.set_xlim(3.3, 25.5); ax.set_ylim(-3, 103); ax.set_yticks([0, 25, 50, 75, 100])
ax = axes[1]
for A, col, lab, lead, dy in ((64, C1, '64 sets', True, 6), (16, C2, '16 sets', False, -7), (4, C3, '4 sets', False, 0)):
    rows = sorted([r for r in t3['numeric'] if r['A'] == A], key=lambda r: r['k'])
    mark(ax, [r['k'] for r in rows], [100 * r['named'] for r in rows], col, lead)
    ax.annotate(lab, (rows[-1]['k'], 100 * rows[-1]['named']), xytext=(5, dy), textcoords='offset points', va='center', fontsize=7.5, color=INK2)
ax.set_title('Numerical questions, reworded + shuffled', loc='left', color=INK, fontweight='semibold')
ax.set_xlabel('Numerical questions in the leak'); ax.set_xticks(range(2, 9)); ax.set_xlim(1.6, 9.6)
fig.tight_layout(); fig.savefig(f'{OUT}/tier3.pdf'); plt.close(fig)

# ------------------------------------------------------------------ Fig: the guarantee
Ts = [10, 100, 1000, 10000]
pa_m = t3['bound_partA']['partA_model']['anytime']; pa_r = t3['bound_partA']['partA_realistic']['anytime']; pk = t3['bound_keys']['anytime']
fig, ax = plt.subplots(figsize=(4.4, 2.75))
ax.plot(Ts, [1 / t for t in Ts], color=INK2, lw=1.2, ls=(0, (4, 3)), zorder=1)
ax.annotate('Proven limit 1/T', (10, 0.1), xytext=(6, 4), textcoords='offset points', fontsize=7.5, color=INK2)
for vals, col, lab, lead in ((pk, C1, 'Answer keys (400,000)', True), (pa_r, C2, 'Short questions, real papers (200,000)', False), (pa_m, C3, 'Short questions, model copies (200,000)', False)):
    ys = [max(vals[str(t)], 1e-6) for t in Ts]
    mark(ax, Ts, ys, col, lead)
ax.set_xscale('log'); ax.set_yscale('log'); ax.set_ylim(2e-6, 0.25)
ax.set_xticks(Ts); ax.set_xticklabels(['10', '100', '1,000', '10,000'])
ax.set_xlabel('Odds bar T (named only against T × N for an outside copy)'); ax.set_ylabel('Outside copies that ever crossed')
ax.grid(True, which='major'); ax.grid(False, which='minor')
handles = [plt.Line2D([], [], color=c, lw=2, marker='o', ms=4, markeredgecolor='white') for c in (C1, C2, C3)] + [plt.Line2D([], [], color=INK2, lw=1.2, ls=(0, (4, 3)))]
ax.legend(handles, ['Answer keys', 'Short questions, real papers', 'Short questions, model copies', 'Proven limit'], loc='lower left', fontsize=7.2)
fig.tight_layout(); fig.savefig(f'{OUT}/guarantee.pdf'); plt.close(fig)

# ------------------------------------------------------------------ Fig: evidence trajectories (anytime)
spec_ = importlib.util.spec_from_file_location('s', os.path.join(HERE, '..', 'sim_tier3.py')); s = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(s)
rng = np.random.default_rng(213)
N, Q, V, EPS, EPS_V = 500, 10, 4, 0.02, 0.05
POS = s.perm_code(Q, N, 4, 2026); VAR = np.random.default_rng(99).integers(0, V, (N, Q))
src = 213; qs = rng.permutation(Q)[:8]
lr = np.zeros((N, len(qs)))
for t, q in enumerate(qs):
    p, v = POS[src, q], VAR[src, q]
    if rng.random() < EPS_V: v = (v + 1) % V
    lr[:, t] = np.where(POS[:, q] == p, math.log((1 - EPS) * Q), math.log(EPS / (Q - 1) * Q)) + np.where(VAR[:, q] == v, math.log((1 - EPS_V) * V), math.log(EPS_V / (V - 1) * V))
cum = np.cumsum(lr, 1) / math.log(10)
order = np.argsort(cum[:, -1])[::-1]
keys = np.load(f'{RES}/answer_keys_500.npy')
lab = t3['key_labels']; master = np.array([lab[j][0] for j in range(20)])
cands = np.vstack([keys, master[None, :]])
ks = rng.permutation(20)[:16]; letters = cands[77, ks].copy(); wrong = rng.random(16) < 0.1
letters[wrong] = (letters[wrong] + rng.integers(1, 4, wrong.sum())) % 4
kl = np.where(cands[:, ks] == letters[None, :], math.log(0.8 * 4), math.log(0.2 / 3 * 4))
kcum = np.cumsum(kl, 1) / math.log(10); korder = np.argsort(kcum[:, -1])[::-1]
fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.8), sharey=True)
for ax, cm, od, nmax, title, xl, bar in ((axes[0], cum, order, len(qs), 'Numbered short questions', 'Lines read', math.log10(1e4 * N)),
                                         (axes[1], kcum, korder, 16, 'Answer key, 1 wrong in 10', 'Answers read', math.log10(1e4 * (N + 1)))):
    x = np.arange(1, nmax + 1)
    for c in od[2:40]:
        ax.plot(x, cm[c], color=GRID, lw=0.8, zorder=1)
    mark(ax, x, cm[od[1]], C2); mark(ax, x, cm[od[0]], C1, True)
    ax.axhline(bar, color=INK2, lw=1.0, ls=(0, (4, 3)))
    ax.annotate('Bar: T × N', (1, bar), xytext=(2, 3), textcoords='offset points', fontsize=7.2, color=INK2)
    gap_ok = [(cm[od[0]][i] >= bar) and (cm[od[0]][i] - max(cm[c][i] for c in od[1:]) >= 4) for i in range(nmax)]
    if any(gap_ok):
        i0 = gap_ok.index(True)
        ax.axvline(i0 + 1, color=C1, lw=0.9, alpha=0.7); ax.annotate(f'named at {i0 + 1}', (i0 + 1, -2.6), xytext=(-3, 0), textcoords='offset points', ha='right', fontsize=7.2, color=C1)
    ax.set_title(title, loc='left', color=INK, fontweight='semibold'); ax.set_xlabel(xl); ax.set_xticks(x[::1] if nmax <= 8 else x[::2])
    ax.set_ylim(-3, 11); ax.set_yticks([-2, 0, 2, 4, 6, 8, 10]); ax.set_yticklabels(['10⁻²', '1', '10²', '10⁴', '10⁶', '10⁸', '10¹⁰'])
axes[0].set_ylabel('Odds against an outside copy')
handles = [plt.Line2D([], [], color=C1, lw=2.2, marker='o', ms=4, markeredgecolor='white'), plt.Line2D([], [], color=C2, lw=1.5, marker='o', ms=3.4, markeredgecolor='white'), plt.Line2D([], [], color=GRID, lw=1.2), plt.Line2D([], [], color=INK2, lw=1, ls=(0, (4, 3)))]
fig.legend(handles, ['Leading college (the true source)', 'Runner-up', 'Other colleges', 'Naming bar'], loc='lower center', ncol=2, bbox_to_anchor=(0.5, -0.02), fontsize=7.6, columnspacing=2.4)
fig.tight_layout(rect=(0, 0.13, 1, 1)); fig.savefig(f'{OUT}/trajectory.pdf'); plt.close(fig)
print('leader is source:', order[0] == src, korder[0] == 77)
print('figs done')
