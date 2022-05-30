# adoption_by_team_task_type.py
# Generates three separate tables—one per team—for “Adoption by Task Type (Jan–Apr 2025)”

import pandas as pd

# 1. Load logs
ai_logs     = pd.read_csv('data/ai_usage_logs.csv',    parse_dates=['date'])
manual_logs = pd.read_csv('data/manual_task_logs.csv', parse_dates=['date'])

# 2. Derive team mapping and combine AI + manual
user_team_map = (
    ai_logs
    .groupby('user_id')['team']
    .agg(lambda s: s.mode().iloc[0])
    .reset_index()
)
manual = (
    manual_logs
    .merge(user_team_map, on='user_id', how='inner')
    .assign(used_ai_tool=False)
)
data = pd.concat([
    ai_logs[['user_id','team','task_type','date','used_ai_tool']],
    manual[['user_id','team','task_type','date','used_ai_tool']]
], ignore_index=True)

# 3. Filter to Jan–Apr 2025
start, end = '2025-01-01', '2025-05-01'
post = data[(data['date'] >= start) & (data['date'] < end)]
post['month'] = post['date'].dt.to_period('M')

# 4. Compute overall (Jan–Apr) adoption by team & task_type
overall = (
    post
    .groupby(['team','task_type'])['used_ai_tool']
    .agg(overall_total_tasks='count', overall_ai_tasks='sum')
    .assign(overall_adoption_rate=lambda df: df['overall_ai_tasks']/df['overall_total_tasks']*100)
    .reset_index()
)

# 5. Compute month‐by‐month rates and pivot wide
monthly = (
    post
    .groupby(['team','task_type','month'])['used_ai_tool']
    .agg(total_tasks='count', ai_tasks='sum')
    .assign(adoption_rate=lambda df: df['ai_tasks']/df['total_tasks']*100)
    .reset_index()
)
months = [pd.Period(m) for m in ['2025-01','2025-02','2025-03','2025-04']]
pivot = (
    monthly
    .pivot(index=['team','task_type'], columns='month', values='adoption_rate')
    .reindex(columns=months, fill_value=0)
    .reset_index()
)
pivot.columns = ['team','task_type'] + [f"{m} %" for m in months]

# 6. Merge overall + monthly into final table
adopt_tt = overall.merge(pivot, on=['team','task_type'], how='left')

# 7. Print one table per team
for team in adopt_tt['team'].unique():
    df = adopt_tt[adopt_tt['team'] == team].copy()
    print(f"\n=== {team} Adoption by Task Type (Jan–Apr 2025) ===\n")
    print(
        df
        .to_string(
            index=False,
            formatters={
                'overall_adoption_rate': '{:.1f}%'.format,
                **{f"{m} %": '{:.1f}%'.format for m in months}
            }
        )
    )
