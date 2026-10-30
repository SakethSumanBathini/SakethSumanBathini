# Merges the per-scenario outputs of sim_coalition.py (run as separate processes) into coalition_results.json
# and prints the comparison with the 1,000-to-1 archive.
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
parts = [json.load(open(os.path.join(HERE, f))) for f in ('coalition_results_mix2.json', 'coalition_results_single_outside.json')]
meta = dict(parts[0]['meta'])
meta['note'] = 'Final decoder (stage 1 + single-source check + stage 2). Scenarios were run as separate processes.'
results = parts[0]['results'] + parts[1]['results']
json.dump(dict(meta=meta, results=results), open(os.path.join(HERE, 'coalition_results.json'), 'w'), indent=1)

old = {(r['scenario'], r['mode'], r['k']): r for r in json.load(open(os.path.join(HERE, 'archive_odds1000', 'coalition_results.json')))['results']}
print('tau', meta['tau_nats'], 'rows', len(results))
for r in results:
    o = old.get((r['scenario'], r['mode'], r['k']), {})
    print(f"{r['scenario']:7s} {r['mode']:10s} k={r['k']:2d} only-true {100 * r['named_only_true_sources']:5.1f} (old {100 * o.get('named_only_true_sources', 0):5.1f})"
          f"  both {100 * r['named_both_colluders']:4.1f}  innocent {100 * r['named_an_innocent']:.2f} (old {100 * o.get('named_an_innocent', 0):.2f})"
          f"  top5 {100 * r['a_true_source_in_single_top5']:5.1f}")
for sc in ('mix2', 'single', 'outside'):
    rows = [r for r in results if r['scenario'] == sc]
    n = sum(round(r['named_an_innocent'] * (3000 if sc == 'mix2' else 1000)) for r in rows)
    tot = len(rows) * (3000 if sc == 'mix2' else 1000)
    print(f'{sc}: innocent named {n} of {tot}')
