# D-009 · Intermediate and wide responsive rules
**Status**: accepted (r2) · density closed (r2.1)
- ≥1800: same shell; inspector stays 420; extra width → more columns / wider values; offer Dense once; no stretched cards; no second pane on the data surface.
- 1440–1799: rail 216 + grid + inspector 372–420.
- 1024–1439: rail 52 icons; inspector **docked push** 340–380; grid uses priority columns and a two-line name cell; toolbar folds secondary controls into View; 44px rows on touch.
- 768–1023: top bar + drawer nav; two-pane workflows keep both panes and move the third into a drawer; inspector becomes a full-height sheet; targets ≥44px.
- <768: task-specific layouts (unchanged).

## Density (owner-approved, r2.1)
- **Standard is the default** for every account.
- **Dense is an explicit user choice**, offered as a one-time suggestion on ≈1800px+ operator displays (and always available in Account → Preferences → Density).
- **Never change a user's density automatically because the viewport width changed** (resize, docking, second monitor). Touch targets on mobile stay ≥44px regardless of density.
**Refs**: Resp-1024, Resp-768, Wide-1920 (5,012-person fixture; shows a user who chose Dense).
