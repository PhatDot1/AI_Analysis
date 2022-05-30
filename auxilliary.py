import pandas as pd

# 1. Load your three sources
users       = pd.read_csv('data/user_directory.csv',    parse_dates=['join_date'])
ai_logs     = pd.read_csv('data/ai_usage_logs.csv',     parse_dates=['date'])
manual_logs = pd.read_csv('data/manual_task_logs.csv',  parse_dates=['date'])

# 2. Derive team from ai_logs
user_team_map = (
    ai_logs
    .groupby('user_id')['team']
    .agg(lambda s: s.mode().iloc[0])
    .to_frame()
)

# 3. Tag manual rows with team (only keep users present in ai_logs)
manual = (
    manual_logs
    .merge(user_team_map, on='user_id', how='inner')
)

# 4. Combine and mark AI vs manual
# 4a) AI logs → source = 'ai' when used_ai_tool==True, else 'manual'
ai_expanded = (
    ai_logs
    .assign(
        source=lambda df: df['used_ai_tool'].map({True: 'ai', False: 'manual'})
    )
)

# 4b) Original manual logs → always manual
manual_expanded = (
    manual
    .assign(source='manual', used_ai_tool=False)
)

# 4c) Concatenate both
all_logs = pd.concat(
    [
        ai_expanded[['user_id','team','task_type','date','used_ai_tool','task_duration_minutes','source']],
        manual_expanded[['user_id','team','task_type','date','used_ai_tool','task_duration_minutes','source']]
    ],
    ignore_index=True
)

# 5. Add month period
all_logs['month'] = all_logs['date'].dt.to_period('M')

# 6. Aggregate per user×month×source
user_monthly = (
    all_logs
    .groupby(['user_id','month','source'])
    .agg(
        task_count     = ('task_type',             'size'),
        total_duration = ('task_duration_minutes','sum')
    )
    .unstack(fill_value=0)
)

# flatten MultiIndex columns
user_monthly.columns = ['_'.join(col).strip() for col in user_monthly.columns.values]
user_monthly = user_monthly.reset_index()

# 7. Compute rates & durations
user_monthly = user_monthly.assign(
    ai_tasks       = user_monthly['task_count_ai'],
    manual_tasks   = user_monthly['task_count_manual'],
    total_tasks    = lambda df: df['ai_tasks'] + df['manual_tasks'],
    adoption_rate  = lambda df: df['ai_tasks'] / df['total_tasks'] * 100,
    ai_avg_dur     = lambda df: df['total_duration_ai'] / df['ai_tasks'].replace(0, pd.NA),
    manual_avg_dur = lambda df: df['total_duration_manual'] / df['manual_tasks'].replace(0, pd.NA)
)

# 8. Join user profile & team
user_monthly_summary = (
    user_monthly
    .merge(users,                        on='user_id', how='left')
    .merge(user_team_map.reset_index(), on='user_id', how='left')
    .sort_values(['user_id','month'])
)

# 9. Save to CSV
output_path = 'data/user_monthly_summary.csv'
user_monthly_summary.to_csv(output_path, index=False)
print(f"✔️ user_monthly_summary saved to {output_path}")
