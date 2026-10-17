# Leak Trace

Interactive explainer for our Seva First Innovation Challenge 2026 entry (South Zone, Theme 4: Shikshit & Kaushal Bharat, Track A).

`index.html` is the whole site in one file: styles, script and fonts are inlined, so it runs anywhere a static file can be served.

## Changes

- **18 Oct 2026.** The decoder in the demo was hardened after an attack test of 148,000 simulated leaks: numbers that simply run 1, 2, 3 are weighed as possibly the leaker's own, a line's wording counts only when it clearly matches one approved wording, and a college is named only at 10,000 to 1 (was 1,000). Innocent colleges named in the test went from 8 to 1. The demo gained "dodge the trace" options (own numbering, rewording, shuffling), and the results section gained the attack table.
- **17 Oct 2026.** First version.
