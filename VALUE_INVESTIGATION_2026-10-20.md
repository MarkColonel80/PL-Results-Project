# Why the value picks have been losing

Investigation completed 20 October 2026, using the original saved forecasts and a corrected historical replay. The main concern is that a large model–price disagreement has been presented too confidently as a betting advantage. Our probabilities have not demonstrated a dependable advantage over the market, especially on the outcomes selected for their apparent value. Next round should be a prospective paper test, with no forced best bet.

The latest two headline watchlist ideas lost, but two losses alone do not establish a broken model: their saved research probabilities imply a 53.4% chance of both losing, assuming independent match outcomes. The wider evidence gives more reason for caution than that short run does.

## What the original forecasts show

Forty manual fixtures survive across GW3, GW4, GW6 and GW7. Twenty-eight had sufficient venue history for published probabilities. All calculation and saved-price timestamps precede kick-off; all 40 fixture and snapshot records were re-read and compared field for field after this investigation, with no changes. These are four published rounds, not a forecast history for all 70 completed current-season matches.

| Forecast on the same 28 games | Brier score | Log loss | Most likely result correct |
| --- | ---: | ---: | ---: |
| Current weekend probability view | 0.6654 | 1.0907 | 11/28 |
| 24-match plus Venue8 research view | 0.6419 | 1.0604 | 9/28 |
| Saved pre-match market with margin removed | **0.6193** | **1.0279** | **13/28** |

Lower scores are better. Brier scores the full three-outcome probability distribution, rather than only whether the favourite won. Twenty-eight games are insufficient to establish long-run performance, but neither model beat this benchmark overall.

The green arrows use the research view and the correct price break-even calculation, `probability − 1 / decimal odds`. There is no newly discovered sign or bookmaker-margin error. The problem is whether the probability itself is reliable enough for the difference to represent an advantage.

| Mechanical research selection from the saved prices | Outcomes | Wins | Hypothetical profit at one unit each |
| --- | ---: | ---: | ---: |
| Every positive price gap | 38 | 12 | +0.68 units |
| Gap at least five percentage points | 13 | 1 | −10.60 units |
| Positive gap at odds above 4.00 | 12 | 1 | −7.00 units |

These are diagnostic calculations, **not a record of recommended or placed bets**. Different rows overlap; a match can contain two mutually exclusive selected outcomes. The five-point rule was fixed for this investigation before historical returns were scored, not a previously adopted live selection rule. Its lone current-season winner was Brighton away at Sunderland, at 2.40. The model expected approximately 4.49 winners among those 13 outcomes; one occurred.

It would therefore be inaccurate to say every displayed value outcome lost. Smaller apparent edges included winners. Equally, retrospectively selecting only those winners would conceal the failure of the strongest apparent signals.

The actual latest watchlist remains separate: Forest–Arsenal draw at 4.00 and Palace away at 6.00 both lost. Palace draw was an alternative, United away lower priority, and an earlier Brentford home watch also lost. No final-lineup promotion, paper stake or actual bet is recorded; none has been invented. See [the settled review](WEEKEND_REVIEW_2026-10-17.md) and its original timestamped records.

## A flaw in the earlier historical validation

The historical research parent `betting_v3_venue8_15_residual_inputs` used a 15-row league-baseline window ordered by kick-off and match ID. A lexically earlier fixture with the same recorded kick-off could contribute its result to the target's prior. Many historical timestamps are date-only, so the ordering cannot establish that these results were known beforehand. This affected 1,119 of 1,673 evaluated windows.

The live weekend SQL already uses the explicit condition `history.kickoff_time < fixture.kickoff_time` and does not contain this particular flaw. It does not explain the current losses directly. It does mean the older cached experiment must not be described as a clean prospective test.

For this investigation, both league priors and their structural-shrinkage midpoint were recalculated from the last 15 strictly earlier matches. Team windows, weights, capped goals, minimum history and Poisson conversion stayed the same. Replaying the original cached calculation first reproduced all 1,673 cached lambda/probability records to a maximum combined error of 1.75e−15. Exact fixture mapping then matched all 1,673 forecasts uniquely by season, date, canonical clubs and final scores; all canonical score/team checks passed. Older odds lack canonical match IDs, so this matching happened locally and did not alter the database.

The correction modestly worsens the scores: development Brier 0.574742 → 0.575468, and the previously inspected 2025/26 stress season 0.638141 → 0.640181. The methodological defect matters even though the numerical effect is small.

The repository research SQL now contains the strict cutoff, with a synthetic PostgreSQL regression test that exercises that actual CTE. Both simultaneous fixtures receive the same prior; their own results, a future result and a sixteenth-old outlier are excluded. All four checks pass. **The materialized view and dependent research caches have not been rebuilt.** Existing cache definitions/results remain archived and require a planned rebuild before reuse. There are also zero same-team duplicate kick-off groups and zero evaluated targets with a historical prior starting within the preceding two hours. No production or frozen forecast was changed.

## What the corrected history says about value

The historical comparison uses 1,433 eligible games in 2019/20–2024/25, then reports 240 games in 2025/26 separately. The latter has been inspected repeatedly and is not an untouched holdout. The historical eligibility restriction starts at each club's 15th league game; it does not validate our present early-season use.

| Strict historical research replay | 2019/20–2024/25 | 2025/26 stress |
| --- | ---: | ---: |
| Model Brier | 0.5755 | 0.6402 |
| Closing no-vig market Brier | **0.5642** | **0.6253** |
| All positive gaps: selections | 1,798 | 283 |
| Model-implied return at those closing average prices | +28.1% | +19.7% |
| Actual hypothetical return | **+0.4%** | **−9.2%** |
| Five-point minimum gap: actual return | +2.4% | −14.9% |
| Excluding odds above 4.00: actual return | −1.3% | −3.3% |

Returns use one hypothetical unit per outcome, retain losing and mutually exclusive outcomes, and use stored Football-Data average prices rather than assuming a personally executable bookmaker quote. Opening-average sensitivity gives +2.1% and −1.5% for all positive gaps: profitability depends materially on the price snapshot. The opening-price sensitivity reuses the latest pre-kickoff model inputs, which may postdate the opening quote; it is not an executable strategy at that earlier price. Historical match stats are retrospectively available versions, not certified original pre-match provider vintages.

The +0.4% development return has a calendar-week block-bootstrap 95% interval of approximately −7.1% to +8.2%; it is not convincing evidence of profit. The stress interval is also broad, −26.7% to +8.3%. Bootstrap intervals are descriptive, based on 2,000 draws with a fixed seed, and cannot remove the earlier model-selection history.

In the expanding-season comparison covering 1,193 test games from 2020/21–2024/25, the raw model's Brier deficit to the market is 0.01234, with a paired week-bootstrap 95% interval of 0.00303 to 0.02149. Both Brier and log loss favour the market. Closing prices have later information than a typical Friday coupon, so this is a demanding benchmark, not a promise that those prices were available when we first formed a watchlist. The 28-game current comparison above uses the same saved pre-match prices as the forecasts' review.

Broad historical probability bins look reasonably calibrated. That does not establish calibration **conditional on disagreeing with bookmakers**. Selecting the largest claimed edges can select our largest estimation errors. The gap between predicted and achieved returns is consistent with that problem; it is not proof that every longshot or underdog is bad value. The seasonal instability is substantial: all-positive closing returns range from −21.8% in 2023/24 to +15.6% in 2024/25.

## Why the current process is vulnerable

**Small and stale venue samples.** Eight home/away appearances can contain only two or three games from this season. The remainder reflects last season's squad, manager and opponents. The bigger historical study deliberately excluded the opening 14 club games, leaving an important validation gap for the way we currently use the model. Early-season performance needs its own strict chronological replay; weaker early-season performance has not been established merely by this audit.

**Finishing and goalkeeper variation can masquerade as team quality.** The existing mixed-goals model can reward unusually low goals conceded relative to xGA. The earlier Bournemouth review already showed that longer-history and xG-only diagnostics weakened its apparent advantage. Those diagnostics are warning checks, not permission to choose whichever forecast best matches the eventual score. The model also has no explicit opponent-strength adjustment to the venue history or quantified player-availability, Europe or keeper adjustment.

**News has been contextual rather than decisive.** Forest's Gibbs-White uncertainty and Palace's Henderson/Mateta concerns were known before kick-off. They were included in conditional watchlists, but there is no recorded check of the confirmed teams and available price that resolved the conditions. Their eventual absences do not establish a numerical injury penalty we can fit from two losses. They do establish that a caveat needs an explicit pre-match decision if it is to affect selection.

**A green arrow is arithmetic, not validation.** Agreement between the current view and the research view is also weak confirmation because they share much of the same data. Nor does a close loss prove the forecast correct: the Forest draw lost even though the game was low scoring. The Palace 5–0 defeat cannot be explained away as merely a narrowly missed draw.

## What should improve next round

1. **Treat the signals as paper picks while the edge is unproven.** Publish every eligible probability and retain the arrows as mathematical price comparisons, but do not automatically call the largest green arrow the best bet. A round with no justified selection is acceptable. Record a paper selection explicitly rather than leaving a watchlist to be interpreted as a recommendation.
2. **Finish the decision when the teams and price are available.** Refresh completed-match inputs first, check club/FPL reports and European rest, then inspect the actual starting goalkeeper, striker and key defenders. Record the bookmaker, executable decimal price, observation time and final watch/paper/pass decision before kick-off. An unresolved condition stays a watch. Append changes; preserve the original assessment.
3. **Show fragility before ranking.** Keep the existing shorter/longer-history and xG-only sensitivity comparisons, show how much venue history predates this season, and flag disagreement or a price advantage that disappears in a reasonable diagnostic. These are transparency checks, not newly validated betting thresholds or replacement probabilities.
4. **Validate the period we actually use.** Rebuild the research dependency chain with strict time cutoffs, reconcile its inputs to the live calculation, and run an early-season chronological test. Freeze a new protocol before choosing an upgrade and use future rounds for prospective evaluation. Keep historical provider vintages and same-bookmaker price provenance where available.
5. **Keep two honest scorecards.** Score all frozen forecasts against a same-time market, and separately settle only explicit pre-recorded paper selections at their observed prices. Track probability quality, conditional calibration, unit profit and matched-bookmaker closing-price movement. Do not backfill wins, reinterpret a lost conditional watch as a pass, increase stakes to recover losses or promise that a filter will make next weekend profitable.

No fixed draw uplift, home advantage tweak, arbitrary injury penalty or new green-arrow threshold has passed this investigation. Model-only recalibration fitted exclusively on previous seasons slightly worsened next-season Brier (0.57473 → 0.57585 across 1,193 games), with uncertainty spanning no change. A fixed 25%-model/75%-market probability blend had a tiny development improvement over the market, but its paired interval spans zero and it worsened the 2025/26 stress comparison. It is not a validated model upgrade or a reason to build bookmaker agreement into our model.

The existing shot-composition work remains research. Chance size, rebounds and game state are plausible future inputs, but the prior signal was small and recent shot/xGOT feeds failed consistency checks. None is a demonstrated quick fix for the current selection problem.

## Evidence and verification

- Original latest selections and match context: [weekend review](WEEKEND_REVIEW_2026-10-17.md), [frozen watchlist](data/weekend-2026-10-17-watchlist.json), [settlement](data/weekend-2026-10-17-settlement.json).
- [Research protocol](research/value-investigation-2026-10-20/PROTOCOL.md), [timing audit amendment](research/value-investigation-2026-10-20/AUDIT_AMENDMENT.md), [full numerical results](research/value-investigation-2026-10-20/results.json), [analysis script](research/value-investigation-2026-10-20/analyse.py) and [input manifest](research/value-investigation-2026-10-20/manifest.json).
- [Corrected research source](scripts/add_v3_venue8_15_residual_research_inputs.sql) and [read-only regression query generator](scripts/test_research_league_prior.py). The generator never executes the source DDL.
- Original inputs, official Football-Data CSVs, replay outputs and a complete local reproducibility archive are retained on this Mac under `outputs/value-investigation-2026-10-20/`. Archive: `/Users/mark2/Documents/Codex/2026-09-10/i-a/outputs/PL-Data-Hub-value-investigation-2026-10-20.zip`.
- Source CSVs: `https://www.football-data.co.uk/mmz4281/{1920,2021,2122,2223,2324,2425,2526}/E0.csv`. Each season has 380 source fixtures. Prices in the main comparison remain the saved database quotes; fresh CSV final scores support exact local fixture matching. [Football-Data historical data](https://www.football-data.co.uk/englandm.php).
- All 40 saved manual fixtures/snapshots are unchanged field for field. Original database fingerprint: `db068f55978649993e07781ea1c79976`. All investigation database calls were read-only SELECTs. Live model formulas, eligibility, saved prices, history, schemas, permissions and research caches were not changed. The only model-related source edit repairs future historical research baselines.
