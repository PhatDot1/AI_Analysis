import pandas as pd
import matplotlib.pyplot as plt

# 1. Load data
users = pd.read_csv('data/user_directory.csv', parse_dates=['join_date'])
ai    = pd.read_csv('data/ai_usage_logs.csv',   parse_dates=['date'])
manual= pd.read_csv('data/manual_task_logs.csv',parse_dates=['date'])

# 2a. Adoption Analysis
# — % of tasks using AI by team
adopt = (
    ai
    .groupby('team')['used_ai_tool']
    .agg(total_tasks='count', ai_tasks=lambda x: x.sum())
    .assign(adoption_rate=lambda df: df['ai_tasks']/df['total_tasks']*100)
    .reset_index()
)
print(adopt)
# → e.g.
#       team  total_tasks  ai_tasks  adoption_rate
# 0  Finance          120        72           60.0
# 1    People         150       105           70.0
# 2     Sales         100        40           40.0

# — Highest & lowest adopters:
highest = adopt.loc[adopt['adoption_rate'].idxmax(), 'team']
lowest  = adopt.loc[adopt['adoption_rate'].idxmin(), 'team']
print(f"Highest: {highest}, Lowest: {lowest}")

# — Trend by team (first vs last month)
ai['month'] = ai['date'].dt.to_period('M')
monthly = (
    ai
    .groupby(['team','month'])['used_ai_tool']
    .mean()
    .reset_index()
)
trend = (
    monthly
    .sort_values(['team','month'])
    .groupby('team')
    .agg(
        first_rate=('used_ai_tool','first'),
        last_rate =('used_ai_tool','last')
    )
    .assign(change_pct=lambda df: (df['last_rate']-df['first_rate'])*100)
    .reset_index()
)
print(trend)
# → e.g. Sales went from 50% → 40% (–10 pts), Finance 55% → 60% (+5 pts)

# 2b. Efficiency Gains
# Compare mean duration when AI was used vs not used
eff = (
    ai
    .groupby(['team','task_type','used_ai_tool'])['task_duration_minutes']
    .mean()
    .reset_index()
    .pivot(index=['team','task_type'], columns='used_ai_tool', values='task_duration_minutes')
    .rename(columns={False:'no_ai', True:'with_ai'})
    .reset_index()
)
eff['time_saved_pct'] = (eff['no_ai'] - eff['with_ai'])/eff['no_ai']*100
print(eff)
# → e.g.
#     team   task_type    no_ai  with_ai  time_saved_pct
# 0  People  forecast_model   75.0    48.0           36.0
# 1  Sales   hiring_pipeline 60.0    55.0           8.3
# …  

# Highlight any task_type with <5% savings
minimal = eff[eff['time_saved_pct'] < 5]
print("Minimal gain:", minimal)

# 2c. AI Quality Assessment
quality = (
    ai[ai['used_ai_tool']]
    .groupby('task_type')['ai_prediction_accuracy']
    .mean()
    .reset_index()
)
print(quality)
# → e.g. budget_reconciliation: 0.77, hiring_pipeline: 0.83, quote_builder: 0.65

# Outliers (<0.70)
low_acc = quality[quality['ai_prediction_accuracy'] < 0.70]
print("Below 0.70:", low_acc)

# 3. Simple Visualizations
plt.figure()
plt.bar(adopt['team'], adopt['adoption_rate'])
plt.title('AI Adoption Rate by Team')
plt.xlabel('Team')
plt.ylabel('% of Tasks with AI')
plt.show()

# And similarly you can loop through `eff` per team for side‐by‐side bars.
