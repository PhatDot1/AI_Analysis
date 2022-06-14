# AI Quality Assessment

To view the [Full Dashboard](ai_quality.py):
```
streamlit run Q1_Technical_Analysis/C_AI_Quality_Assessment/ai_quality.py
```

## Average AI Prediction Accuracy by Task Type

| Task Type               | Average Accuracy |
|-------------------------|------------------|
| **forecast_model**      | 0.80             |
| **hiring_pipeline**     | 0.79             |
| **quote_builder**       | 0.79             |
| **budget_reconciliation** | 0.77           |

## Outliers and Concerning Trends

### 1. High Rates of Low-Accuracy Predictions (< 0.70)

- **By Team & Task**  
  - **Finance / quote_builder:** 37.5% of predictions < 0.70 
  - **Finance / hiring_pipeline:** 36.1% < 0.70 
  - **People / budget_reconciliation:** 32.1% < 0.70  
  - **Sales / budget_reconciliation:** 28.0% < 0.70
  - **Sales / hiring_pipeline:** 27.0% < 0.70 

- **By Team (overall)** 
  - **Finance:** 28.6% of all Finance predictions below 0.70 
  - People: 22.7% 
  - Sales: 24.0%  

- **By Task (overall)** 
  - **hiring_pipeline:** 28.4% below 0.70
  - **budget_reconciliation:** 27.5% 
  - **quote_builder:** 26.3%
  - **forecast_model:** 18.0% 

> **Insight:** Forecast_model tasks exhibit the strongest baseline performance, with the fewest low‐accuracy outcomes.

---

> **Note:** Two critical challenges in modern AI workflows are **semantic drift** (in-session topic coherence) and **concept drift** (evolving data distributions). By tracking task duration and usage dates against prediction accuracy, we give data analysts the core metrics needed to surface and address these inherent flaws in generative AI tools.


### 2. Task-Duration vs. Prediction Accuracy

To detect semantic drift, I modeled **AI prediction accuracy** as a function of **task duration**. The fitted slopes (`slope_acc_per_min`) are expressed in Δaccuracy (decimal) per minute; the following columns convert these to percentages per 1 min and per 10 min:


| Team     | Task Type               | Slope (Δ dec/min) | Δ accuracy per 1 min | Δ accuracy per 10 min |
|----------|-------------------------|-------------------|----------------------|-----------------------|
| People   | hiring_pipeline         | +0.002687         | +0.27 %              | +2.69 %               |
| People   | budget_reconciliation   | –0.002457         | –0.25 %              | –2.46 %               |
| Finance  | hiring_pipeline         | –0.002078         | –0.21 %              | –2.08 %               |
| Finance  | budget_reconciliation   | –0.001481         | –0.15 %              | –1.48 %               |
| People   | forecast_model          | –0.001287         | –0.13 %              | –1.29 %               |
| Sales    | forecast_model          | –0.000977         | –0.10 %              | –0.98 %               |
| Sales    | quote_builder           | –0.000973         | –0.10 %              | –0.97 %               |
| Finance  | quote_builder           | –0.000857         | –0.09 %              | –0.86 %               |
| People   | quote_builder           | –0.000274         | –0.03 %              | –0.27 %               |
| Sales    | hiring_pipeline         | +0.000119         | +0.01 %              | +0.12 %               |
| Sales    | budget_reconciliation   | +0.000085         | +0.01 %              | +0.08 %               |
| Finance  | forecast_model          | +0.001092         | +0.11 %              | +1.09 %               |

> - The **largest negative slopes** indicate the fastest accuracy degradation as tasks lengthen.
>   - **People / budget_reconciliation (–0.00246):** ~0.25 % drop per minute (≈2.5 % over 10 min) 
>   - **Finance / hiring_pipeline (–0.00208):** ~0.21 % drop per minute 
>   - **Finance / budget_reconciliation (–0.00148):** ~0.15 % drop per minute 
>
> - **Positive slopes** indicate accuracy improves with longer duration:
>   - Some of this may be random noise, or it may suggest that longer tasks reflect more thorough, deliberate AI usage.  
>
> - **Near-zero slopes** (< |0.001|) suggest duration has minimal effect (e.g., Sales / quote_builder).  
>
> **Note:** All slopes translate to < 1.5 % change over a 10-minute increase (overall ≈ −0.5 %), so duration alone is unlikely to threaten accuracy unless sessions are extended dramatically.

Most task-duration effects remain small, and only under extreme extensions might accuracy dip below practical thresholds (e.g., 0.7). Given that even the steepest declines average under 1.5 %, this isn’t an immediate concern—but it’s worth monitoring for outliers.

#### Potential Takeaways

- **Introduce intermediate checkpoints** in **budget_reconciliation** and **hiring_pipeline** workflows (People & Finance) to limit accuracy degradation during long sessions.
- **Investigate** why **People / hiring_pipeline** improves with time—there may be best practices or model warm-up effects to generalize.
- **Maintain** current workflows for tasks with near-zero slopes but **monitor** as data volume and session lengths grow.
- To refine these recommendations, we’ll need deeper insight into the underlying AI pipelines and user workflows to avoid over-interpreting these correlations.

### 3. Temporal Anomalies

-- analysis to detect Concept Drift --

- **May 2025 Forecast Model:** The only data point in May for Forecast Model is 0.65 (2025-05-01, 35 min task), which falls **15 points below** its four-month average (0.80). 
  > This appears to be an **outlier** rather than a sustained drop, since it is a single observation.

- **Monthly Stability:** Across teams and tasks, prediction accuracy has remained largely stable (± 0.03) from January to April 2025, with no clear downward trend. It would be ideal to continue collecting data to see any potential emergence.

---

## Overall Summary

1. **Overall Performance** sits between 0.77–0.80 by task.
2. **Finance** exhibits the greatest proportion of low‐accuracy outliers, especially in **quote_builder** and **hiring_pipeline** tasks. 
3. **Forecast_model** is the most reliable task type, with only 18% of predictions below 0.70.
4. **Task duration** shows modest negative correlations with accuracy in Finance and Sales, but these are unlikely to be operationally significant at current task lengths.
5. A single **May 2025** data point for Forecast Model (0.65) should be treated as an outlier.
