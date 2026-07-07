# 🏯 唐太宗 v3.0 · Causal Audit Report (v31)

> **Subject:** Affective Publics under Policy Shocks: Skeptical Inertia
> **Version:** v31 (vs v30 baseline)
> **Review Date:** 2026-06-17
> **Auditor:** Causal Inference Subagent

---

## Executive Summary

v31 represents a **meaningful but incomplete** improvement in causal inference quality. The ITS result has shifted from borderline-significant (p=.042, fragile to weekday controls) to robustly significant (p=.002, survives all sensitivity checks). However, this improvement comes with a critical interpretive twist: the DV has changed from mean sentiment score to share of positive comments, meaning the two versions' results are **not directly comparable** on the coefficient level. More importantly, the v31's statistical significance does not cure the study's fundamental design limitations—short baseline (23 days), no concurrent-event controls, and SnowNLP's low accuracy—but it does change the nature of the argument from "proving the null" to "bounding a small effect." The causal inference score rises from **3/10 to 4.5/10**.

---

## 1. ITS Results: Why Did They Change?

### 1.1 Model Specification Check

| Element | v30 | v31 | Assessment |
|:--------|:----|:----|:-----------|
| **Dependent Variable** | Mean sentiment score (continuous, 0-1) | Share of positive comments (proportion, 0-1) | ❌ **Different DVs** |
| **Regression formula** | Standard ITS linear: Y_t = β₀ + β₁T + β₂D + β₃P + ε | Likely same formula structure | Presumably same |
| **HAC SE** | Standard OLS SE? | HAC SE = 0.023 | ✅ Improvement |
| **Weekday controls** | p=.057 (not robust) | p=.002 (robust) | ✅ Big improvement |
| **FDR correction** | Not applied | q=.011 | ✅ Improvement |

### 1.2 The DV Change: "Mean Sentiment Score" vs "Share of Positive Comments"

**This is the most critical finding of this audit.** v30 and v31 use different DVs:

- **Mean sentiment score** (v30): Average of SnowNLP's continuous sentiment score (0-1) across all comments on day t. A change from 0.40 to 0.436 means the *average* comment became slightly more positive.
- **Share of positive comments** (v31): Proportion of comments exceeding a strict positivity threshold (>0.8 on SnowNLP scale). A b=0.071 means positive comments rose by 7.1 percentage points with each policy shock.

**Why this matters:**

1. **Scale interpretation differs fundamentally.** Changes in mean sentiment can be driven by subtle shifts across the entire distribution (e.g., many comments moving from 0.35 to 0.38). Changes in positive share are driven only by the tail of the distribution crossing a high threshold (0.8+).

2. **Coefficients are not comparable.** v30's b=0.036 is in "mean sentiment units" (a 3.6 percentage point movement on a 0-1 scale); v31's b=0.071 is in "positive share units" (a 7.1 percentage point increase in the proportion of comments classified as positive). These are mathematically different constructs.

3. **The "2.7 percentage point" claim cited in your task description** is the v31 result (positive share rose ~2.7 pp). But was this reported alongside the mean sentiment result? If only positive share is reported, the reader cannot assess whether mean sentiment also moved.

4. **SnowNLP's positive accuracy bias interacts with this DV choice.** The task memo mentions SnowNLP overestimates positive sentiment. If the DV is *share of positive comments*, and SnowNLP tends to over-positivize, then the detected 2.7 pp rise may partly reflect measurement artifact rather than true sentiment change. The v31 paper apparently addresses this with the "bias direction argument" (overestimate → detected effect is an upper bound), which is clever but not a complete defense.

### 1.3 Are the Two Versions' Conclusions Consistent?

**In spirit, yes—in magnitude, unclear.**

- v30: "A tiny increase in mean sentiment that's barely distinguishable from noise"
- v31: "A modest increase in positive comment share that's distinguishable from noise"

Both detect *some* positive movement. The difference is that v31 packages this as a real finding ("sentiment warms") while v30 called it indistinguishable from noise. The underlying data pattern is likely similar; the frames are different.

**Recommendation:** The paper should report **both** mean sentiment and positive share in a unified model (e.g., one primary DV + robustness check with the other), or transparently explain why one was chosen over the other. The reader needs to understand whether the effect is in the mean, the tail, or both.

---

## 2. Does the New p-Value Change the Causal Identification Story?

### 2.1 p=.002 Is Nice, But It's Not a Magic Wand

| Causal ID Threat | v30 Status | v31 Status | Effect of p=.002 | 
|:----------------|:-----------|:-----------|:-----------------|
| Short 23-day pre-intervention baseline | ❌ Weak | ❌ Unchanged | **Zero impact** — p-value cannot lengthen the baseline |
| No concurrent-event controls | ❌ Missing | ❌ Unchanged | **Zero impact** — p-value cannot account for the Fed, election, etc. |
| HAC SE + weekday controls | 🟡 Fragile | ✅ Robust | **Positive** — model is more reliable |
| Placebo test support | ⚠️ 37.5% noise | ✅ 12.8% noise | **Positive** — less likely to be a false positive |
| SnowNLP measurement error | ❌ 36.7% acc | ❌ Unchanged | **Zero impact** — p-value is still computed from noisy data |

The p-value improvement is **real but narrow**. It tells us the observed jump on the first intervention day is unlikely to be random chance. It does NOT tell us:
- Whether the jump is caused by the intervention specifically, vs. any other event on that day
- Whether the pre-intervention trend is correctly characterized (23 days is still too short)
- Whether the SnowNLP measurement error exaggerates or masks the effect

### 2.2 The 23-Day Baseline Problem: Not Cured

The short baseline remains the **single most serious causal identification weakness**. With 23 pre-intervention observations:

- **Trend estimation is highly uncertain.** The 95% CI around the pre-slope covers a wide range of possible trajectories.
- **Seasonal patterns cannot be identified.** Weekly cycles require at least 14 days to observe two full cycles; 23 days gives barely enough.
- **Pandemic/economic regime shifts cannot be distinguished from the pre-intervention trend.** If sentiment was already trending slightly up in September 2024 (after the market collapse in August 2024), the "intervention effect" is just the continuation of a prior trend.

**p=.002 makes this problem more visible, not less.** A strong statistical result on a weak design is not a strong result—it's a fragile one.

---

## 3. Effect Size Assessment

### 3.1 Is a 2.7 pp Rise in Positive Comments Substantively Meaningful?

| Benchmark | Comparison | Assessment |
|:----------|:-----------|:-----------|
| Baseline positive rate | ~10-12% → ~13-15% | Relative increase of ~25-30% — **not trivial** |
| Natural daily volatility | ~±2-3 pp (typical for sentiment time series) | Rise is near the upper bound of daily noise — **modest** |
| Policy shock literature (stock market) | Event returns of 2-8% on A-share policies | Smaller than market reactions — **small effect** |
| Sentiment analysis literature | 0.1-0.2 SD considered small | Need to compute Cohen's d from available data |
| SnowNLP positive bias | Effect is an upper bound | True effect likely smaller — **even smaller** |

**Verdict:** A 2.7 pp rise in positive comment share is a **small-to-moderate** effect by usual social science standards. In sentiment analysis specifically, 2-3% movements are common daily noise. The key argument is not the size of the effect, but **its shape**: the effect loads at the first intervention only, then does not accumulate or escalate with subsequent interventions.

### 3.2 How Would a Reviewer See This?

A **favorable reviewer** might say:
> "The effect is modest but consistent across multiple tests (ITS, placebo, individual event checks, strict thresholds). The interesting finding is not how big it is, but how bounded it is — it appears once and then plateaus."

A **hostile reviewer** might say:
> "You're claiming a 'warming' that is barely outside the daily noise band, computed by a sentiment classifier with 36.7% overall accuracy and 14% positive precision. The effect size is too small to be substantively meaningful, even if statistically significant."

**The burden is on the authors** to demonstrate that 2.7 pp is not just statistically significant but substantively interpretable. The best defense is the **pattern argument**: the fact that it only loads once and doesn't build is the real finding, not the absolute magnitude.

### 3.3 "If the Effect Is Trivial, Does the Paper's Argument Still Hold?"

**Yes, remarkably.** The paper's core claim is not "sentiment moved a lot" but "sentiment moved in a specific bounded way that reveals the nature of skeptical inertia." A trivial effect with a specific temporal signature is *more* informative than a large effect that persists.

- **Re-frame:** "The effect is small *because* skeptical inertia caps emotional responses. A large effect would have contradicted our theory."
- **Risk:** Some reviewers will still ask: "If the effect is this small, what's the practical importance for understanding Chinese social media publics?"

---

## 4. The Null Result Re-Interpretation

### 4.1 From "Proving the Null" to "Bounding the Effect"

| Dimension | v30 (Null) | v31 (Bounded Effect) | Implication |
|:----------|:-----------|:---------------------|:------------|
| **Statistical claim** | No distinguishable effect | Significant small effect | v31 is on stronger statistical ground |
| **Theoretical claim** | "Nothing happens" | "Something small happens then stops" | v31 is more nuanced and plausible |
| **Burden of proof** | Must prove equivalence to zero | Must show effect is bounded | Lighter: rejecting H₀ is easier than confirming H₀ |
| **Reviewer criticism** | "You didn't find anything because your tools are bad" | "Even if your tools are bad, you found something" | Weaker criticism |

### 4.2 TOST Equivalence Test: Still Needed?

| If paper still claims... | TOST needed? | Why |
|:-------------------------|:-------------|:----|
| "Sentiment does not respond" | ✅ **Yes, critical** | Need to confirm equivalence to zero |
| "Sentiment responds once, modestly" | ⚠️ **Useful but optional** | Would bound the maximum plausible effect |
| "The response is bounded and non-accumulating" | ✅ **Yes, for the non-accumulation part** | Need to show Day+30 ≡ Day+1 |

**Revised recommendation:** The v31 paper's primary claim is no longer "no effect" but "bounded, non-accumulating effect." TOST is now most useful for the **non-accumulation and non-escalation** claims — showing that effect at intervention N (N>1) is equivalent to zero, or that the post-interruption trend is indistinguishable from flat.

### 4.3 Bayesian Factor: Still Needed?

Bayes factors are now:
- **Less critical for the main ITS claim** (since p=.002 already supports rejecting H₀)
- **More useful for the non-accumulation sub-claim** (BF for H₀: no escalation vs H₁: building)
- **Still valuable for the placebo comparison** (BF showing that 12.8% placebo-exceeding rate is consistent with a true effect)

**Revised recommendation:** Add Bayes factors for:
1. The non-accumulation: BF₀₁ for "intervention #4 effect = 0"  
2. The boundedness: BF for "post-interruption trend slope = 0"
3. (Optional but valuable) Bayes factor comparing the v31 model to a model where all four interventions have independent effects

---

## 5. Concurrent-Events Control: Re-Assessment Under v31

### 5.1 Does a Significant ITS Result Increase or Decrease the Confounding Threat?

**Counterintuitively, a significant result INCREASES the confounding threat.**

| Scenario | Confounding threat | Why |
|:---------|:------------------|:----|
| v30: p=.042, fragile | 🔴 High | Borderline result could easily be confounded into or out of significance |
| v31: p=.002, robust | 🔴 **Still high; changed character** | A strong result that remains after placebo testing is *less likely* to be pure noise — but it could be a strong *confounded* result. Confounding doesn't just create significance; it can amplify or redirect it. |

**The key logical problem:** If the first policy intervention (September 24, 2024) coincided with:
- The US Federal Reserve's September 2024 FOMC meeting (rate cut decision)
- A major Chinese economic data release
- The Lunar New Year preparation cycle
- A geopolitical event (US-China trade friction rhetoric)

...then the detected "sentiment warming" on that exact day is **not attributable to the policy intervention** even with p=.002.

### 5.2 What Would a Reviewer Argue?

> "Your ITS identifies a one-day jump in positive sentiment on September 24. September 24 was the day the Fed cut rates by 50bp — the first rate cut in four years. Chinese media covered this extensively. Your 'policy shock' effect is confounded with the single largest global monetary policy event of the year."

**This is a correct criticism.** The A-share market interventions in Fall 2024 were part of a larger global macroeconomic policy cycle. Without controlling for:
- Domestic: CSI300 returns, trading volume, VIX-style volatility index
- International: FOMC meeting dates, S&P 500 returns, US-China policy events
- Seasonal: holiday effects, end-of-quarter effects, Chinese New Year set-up period

...the ITS remains fundamentally unidentifiable.

### 5.3 How Significant Is This Gap Now?

| Before (v30) | After (v31) |
|:-------------|:------------|
| "You have a weak result + no controls = probably just noise" | "You have a strong result + no controls = probably real but possibly misattributed" |
| The confounding threat was used to *discount* the result | The confounding threat is now used to *re-attribute* the result |
| Easier to dismiss: "it's probably nothing" | Harder to dismiss: "something happened, but was it your intervention?" |

**The absence of controls is now a more dangerous problem**, not less. Before, a critic could say "your result is too weak to matter." Now they say "your result is evidence of something — but not necessarily what you think it is."

---

## 6. Overall Causal Inference Strength: Re-Scored

### 6.1 Revised Scoring (v31)

| Causal Inference Dimension | v30 Score | v31 Score | Change | Rationale |
|:---------------------------|:--------:|:--------:|:------:|:----------|
| **1. Internal validity (ITS design)** | 2/10 | 3/10 | +1 | p=.002 + placebo at 87th percentile is credible, but 23-day baseline still weak |
| **2. Statistical conclusion validity** | 3/10 | 5/10 | +2 | HAC SE, FDR, weekday robustness — model is properly specified |
| **3. Measurement validity (DV)** | 4/10 | 4.5/10 | +0.5 | SnowNLP still 36.7%, but positive share is a cleaner construct + bias-direction defense |
| **4. Confounding control** | 1/10 | 1/10 | 0 | **No progress.** Zero control variables remain. |
| **5. Effect bounding** | 2/10 | 4/10 | +2 | Now estimates magnitude (2.7 pp) rather than claiming zero. But still no TOST/Bayes. |
| **6. Sensitivity/robustness** | 4/10 | 6/10 | +2 | Placebo improved (200→2000 draws, 37.5%→12.8%), strict thresholds added |
| **7. Theory-evidence alignment** | 5/10 | 7/10 | +2 | v31's narrative ("bounded warm-up") fits the evidence better than v30's "zero" |
| **Composite Causal Score** | **3.0/10** | **4.5/10** | **+1.5** | Meaningful but still below any threshold for credible causal inference |

### 6.2 What Changed (and What Didn't)

**Improvements:**
- Statistical modeling: HAC SE, FDR, weekday controls → model is no longer fragile
- Placebo test: 2,000 draws, 87th percentile → less noise-like
- SnowNLP bias argument: clever framing
- Narrative alignment: effect pattern matches theory better than null

**Unchanged weaknesses:**
- ❌ 23-day pre-intervention baseline → trend estimation is unreliable
- ❌ Zero concurrent-event controls → confounding is a first-order threat
- ❌ SnowNLP 36.7% accuracy → measurement error is still large
- ❌ LDA coherence 0.31-0.49 → topic inference is unreliable
- ❌ No TOST/Bayes → non-accumulation claim is untested
- ❌ No sensitivity analysis with alternative DV → "positive share only" is a specification choice that could affect results

### 6.3 Remaining "Red Line" Gaps

These are the gaps that **v31 has not addressed and that prevent the causal inference score from exceeding 5/10:**

1. **🟥 23-day pre-intervention baseline** — This is structural. Without at least 30-40 pre-intervention data points, ITS trend estimation is fundamentally unreliable. The significant p-value is computed from a weak foundation.

2. **🟥 No control variables** — This is immediately fixable (add CSI300 returns, volume, holiday dummies, FOMC dummies) but has not been done. A reviewer will flag this within 30 seconds of reading the Methods section.

3. **🟥 Positive share as sole DV** — If only positive share moves but mean sentiment does not, the story changes. This needs to be transparently reported.

4. **🟥 No TOST for non-accumulation** — The v31's most interesting claim ("it warms once and that is all") requires demonstrating that later interventions produce zero additional effect. Without formal equivalence testing, this claim is based on visual inspection of non-significant p-values.

---

## 7. Recommendations for v32

### P0 — Fix Immediately

| # | Action | Impact on Causal Score | Effort |
|:-:|:-------|:---------------------:|:------|
| 1 | **Add 5-6 control variables** (CSI300 return, volume, holiday, FOMC, election) | +1.5 | 1-2 days |
| 2 | **Report both DVs** (mean sentiment AND positive share) or justify choice transparently | +1 | 0.5 day |
| 3 | **Run TOST for non-accumulation** (effect at intervention N vs zero for N=2,3,4) | +1 | 1 day |
| 4 | **Calculate Bayes factor for post-interruption trend = 0** | +0.5 | 0.5 day |

### P1 — Strongly Recommended

| # | Action | Impact | Effort |
|:-:|:-------|:------:|:------|
| 5 | **Extend data** to July 2024 (60-day pre baseline) | +2 | 3-5 days |
| 6 | **Conduct specification curve analysis**: vary window lengths, DV definitions, inclusion of controls | +1 | 3 days |
| 7 | **Compute Cohen's d or other standardized effect size** for the 2.7 pp rise | +0.5 | 0.5 day |

### P2 — If Feasible

| # | Action | Impact | Effort |
|:-:|:-------|:------:|:------|
| 8 | **ARIMA-based ITS** instead of linear regression (better fit for autocorrelated daily data) | +0.5 | 2 days |
| 9 | **Subsample analysis**: split by comment type, user activity level | +0.5 | 2 days |

---

## 8. Summary

### Causal Inference Score: v30 = 3/10 → v31 = 4.5/10

The improvement is real but narrow. v31 has upgraded from "barely significant, fragile" to "robustly significant, well-specified" on the statistical modeling side, but has made **zero progress** on the fundamental design weaknesses (short baseline, no controls) that were identified in v30.

**If a reviewer were to read v31 today, their likely response:**

> "Your ITS is now properly estimated and your placebo is convincing within its limits. Congratulations — that's real progress. But you still haven't controlled for concurrent events, your pre-intervention trend is estimated from only 23 days, and your DV changed without explanation. I cannot accept a causal claim from this design as currently presented."

**Recommended framing for the paper:** Do not overclaim on causal identification. The paper should position the ITS result as one piece of convergent evidence within a larger qualitative-interpretive framework, not as a stand-alone causal identification strategy. The real strength of the paper remains the theoretical contribution (skeptical inertia) and the expression typology, not the ITS causal estimate.

---

## Appendix: Quick Reference Numbers

| Metric | v30 | v31 | Comparable? |
|:-------|:---:|:---:|:-----------:|
| ITS coefficient b | 0.036 | 0.071 | ❌ Different DVs |
| DV scale | Mean sentiment (0-1) | Share positive (0-1) | ❌ |
| p-value | 0.042 | 0.002 | Not directly (different DV) |
| Weekday-controlled p | 0.057 | 0.002 | Not directly |
| HAC SE | Not reported | 0.023 | ❌ |
| FDR q-value | N/A | 0.011 | ✅ |
| Placebo exceedance rate | 37.5% (200 draws) | 12.8% (2,000 draws) | ⚠️ Partially (different # draws) |
| Placebo percentile | N/A | 87th | — |
| Subjective effect size | 2.7 pp (if mean score) | 2.7 pp (positive share) | ⚠️ Same pp but different meaning |
| SnowNLP accuracy | 36.7% | 36.7% | ✅ Same (unchanged) |
| TOST equivalence | ❌ | ❌ | ✅ Same (both missing) |
| Control variables | ❌ | ❌ | ✅ Same (both missing) |
| 23-day baseline | ❌ | ❌ | ✅ Same (both weak) |

### Key Takeaway

The v31 improvements are **statistical, not structural**. The model is better estimated, but the design is not better identified. The causal score rises from 3 to 4.5 because the model is more credible within its limits, but the limits themselves have not expanded.
