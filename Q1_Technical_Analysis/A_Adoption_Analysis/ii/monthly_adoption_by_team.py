# monthly_adoption_by_team.py
# Computes Monthly Adoption Rates, Overall & Various Δ‐Metrics by Team

import pandas as pd

# 1. Load the user×month summary
ums = pd.read_csv('data/user_monthly_summary.csv', parse_dates=['month'])

# 2. Restrict to the 2025-01 through 2025-04 window (ignore partial May)
start = pd.Timestamp('2025-01-01')
end   = pd.Timestamp('2025-04-01')
ums   = ums[(ums['month'] >= start) & (ums['month'] <= end)]

# 3. Aggregate to get monthly adoption rates
team_monthly = (
    ums
    .groupby(['team','month'])
    .agg(
        total_tasks=('total_tasks', 'sum'),
        ai_tasks   =('ai_tasks',    'sum')
    )
    .assign(adoption_rate=lambda df: df['ai_tasks'] / df['total_tasks'] * 100)
    .reset_index()
    .sort_values(['team','month'])
)

# 4. Show the monthly rates
print("\n📊 Monthly Adoption Rates by Team (2025-01 → 2025-04):")
print(
    team_monthly
    .to_string(
        index=False,
        formatters={'adoption_rate': '{:.1f}%'.format}
    )
)

# 5. Compute overall totals across Jan-Apr for each team
overall = (
    team_monthly
    .groupby('team')
    .agg(
        total_tasks_overall=('total_tasks', 'sum'),
        ai_tasks_overall   =('ai_tasks',    'sum')
    )
    .assign(overall_adoption_rate=lambda df: df['ai_tasks_overall'] / df['total_tasks_overall'] * 100)
    .reset_index()
)

print("\n📊 Overall Adoption by Team (Jan-Apr 2025):")
print(
    overall
    .to_string(
        index=False,
        formatters={'overall_adoption_rate':'{:.1f}%'.format}
    )
)

# 6. Build KPI table with all Δ variants
records = []
for team, df in team_monthly.groupby('team'):
    df = df.set_index('month')
    # rates at each month
    jan = df.at[start, 'adoption_rate']
    feb = df.at[pd.Timestamp('2025-02-01'), 'adoption_rate']
    mar = df.at[pd.Timestamp('2025-03-01'), 'adoption_rate']
    apr = df.at[end,   'adoption_rate']
    # absolute difference Apr–Jan (%-points)
    abs_change = apr - jan
    # relative % change Apr vs Jan
    rel_change = (apr - jan) / jan * 100 if jan != 0 else float('nan')
    # month-to-month absolute deltas
    abs_deltas = [feb - jan, mar - feb, apr - mar]
    avg_mom_abs = sum(abs_deltas) / len(abs_deltas)
    # month-to-month relative deltas
    rel_deltas = [
        (feb - jan) / jan * 100 if jan != 0 else float('nan'),
        (mar - feb) / feb * 100 if feb != 0 else float('nan'),
        (apr - mar) / mar * 100 if mar != 0 else float('nan'),
    ]
    avg_mom_rel = sum([x for x in rel_deltas if pd.notna(x)]) / len([x for x in rel_deltas if pd.notna(x)])
    records.append({
        'team':                  team,
        'Jan_rate':              jan,
        'Feb_rate':              feb,
        'Mar_rate':              mar,
        'Apr_rate':              apr,
        'Δ abs % (Apr–Jan)':     abs_change,
        'Avg MoM abs %':         avg_mom_abs,
        'Δ rel % (Apr–Jan)':     rel_change,
        'Avg MoM rel %':         avg_mom_rel,
    })

trend = pd.DataFrame(records)

# 7. Print the full KPI table
print("\n📈 Adoption Change KPIs by Team:")
print(
    trend
    .to_string(
        index=False,
        formatters={
            'Jan_rate':            '{:.1f}%'.format,
            'Feb_rate':            '{:.1f}%'.format,
            'Mar_rate':            '{:.1f}%'.format,
            'Apr_rate':            '{:.1f}%'.format,
            'Δ abs % (Apr–Jan)':   '{:+.1f}%'.format,
            'Avg MoM abs %':       '{:+.1f}%'.format,
            'Δ rel % (Apr–Jan)':   '{:+.1f}%'.format,
            'Avg MoM rel %':       '{:+.1f}%'.format,
        }
    )
)
