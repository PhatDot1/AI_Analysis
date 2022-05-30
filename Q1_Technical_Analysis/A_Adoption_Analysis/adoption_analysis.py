# load relevant data
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

st.set_page_config(page_title="AI Adoption Dashboard", layout="wide")
st.title("🚀 AI Tool Adoption & Efficiency Dashboard")

users       = pd.read_csv('data/user_directory.csv', parse_dates=['join_date'])
ai_logs     = pd.read_csv('data/ai_usage_logs.csv',    parse_dates=['date'])
manual_logs = pd.read_csv('data/manual_task_logs.csv', parse_dates=['date'])

# attach user names & teams
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

post = data[(data['date'] >= '2025-01-01') & (data['date'] < '2025-05-01')].copy()
post['month'] = post['date'].dt.to_period('M')

# a) i) adoption by team
overall_tt = (
    post
    .groupby(['team','task_type'])['used_ai_tool']
    .agg(total_tasks='count', ai_tasks='sum')
    .assign(overall_adoption_rate=lambda df: df['ai_tasks']/df['total_tasks']*100)
    .reset_index()
)

chart_tt = (
    alt.Chart(overall_tt)
    .mark_bar()
    .encode(
        x=alt.X('team:N', title='Team'),
        xOffset='task_type:N',
        y=alt.Y('overall_adoption_rate:Q', title='Adoption Rate (%)'),
        color=alt.Color('task_type:N', title='Task Type'),
        tooltip=[
            'team',
            'task_type',
            alt.Tooltip('overall_adoption_rate:Q', format='.1f', title='Adoption %')
        ]
    )
    .properties(height=300)
)

# plot adoption rates
st.altair_chart(chart_tt, use_container_width=True)

st.subheader("Breakdown: Adoption by Task Type (Jan–Apr 2025)")
months = [pd.Period(m) for m in ['2025-01','2025-02','2025-03','2025-04']]

monthly_tt = (
    post
    .groupby(['team','task_type','month'])['used_ai_tool']
    .agg(total_tasks='count', ai_tasks='sum')
    .assign(adoption_rate=lambda df: df['ai_tasks']/df['total_tasks']*100)
    .reset_index()
)
pivot_tt = (
    monthly_tt
    .pivot(index=['team','task_type'], columns='month', values='adoption_rate')
    .reindex(columns=months, fill_value=0)
    .reset_index()
)
pivot_tt.columns = ['team','task_type'] + [f"{m} %" for m in months]

adopt_tt = overall_tt.merge(pivot_tt, on=['team','task_type'], how='left')
adopt_team_raw = (
    post
    .groupby('team')['used_ai_tool']
    .agg(total_tasks='count', ai_tasks='sum')
    .reset_index()
)

for team in adopt_tt['team'].unique():
    st.markdown(f"**{team} — Adoption by Task Type**")
    df = adopt_tt[adopt_tt['team']==team].drop(columns='team')
    st.dataframe(
        df.style.format({
            'total_tasks':           '{:,}',
            'ai_tasks':              '{:,}',
            'overall_adoption_rate': '{:.1f}%',
            **{f"{m} %": '{:.1f}%' for m in months}
        }),
        height=240
    )
    row = adopt_team_raw[adopt_team_raw['team']==team].iloc[0]
    rate = row.ai_tasks / row.total_tasks * 100
    st.markdown(
        f"**Overall Jan–Apr 2025 for {team}:** "
        f"{row.total_tasks:,} tasks, "
        f"{row.ai_tasks:,} AI tasks → "
        f"{rate:.1f}% adoption"
    )

# a) ii) highest & lowest
ums_totals = (
    post
    .groupby('team')['used_ai_tool']
    .agg(total_tasks='count', ai_tasks='sum')
    .assign(overall_adoption_rate=lambda df: df['ai_tasks']/df['total_tasks']*100)
    .reset_index()
)
st.subheader("📊 Overall Adoption by Team (Jan–Apr 2025)")
st.dataframe(
    ums_totals.style.format({'overall_adoption_rate':'{:.1f}%'}),
    use_container_width=True
)

adopt_team = ums_totals.copy()
high = adopt_team.loc[adopt_team['overall_adoption_rate'].idxmax()]
low  = adopt_team.loc[adopt_team['overall_adoption_rate'].idxmin()]

c1, c2 = st.columns(2)
c1.metric("🏆 Highest Adopting Team", high.team, f"{high.overall_adoption_rate:.1f}%")
c2.metric("📉 Lowest Adopting Team",  low.team,  f"{low.overall_adoption_rate:.1f}%")

# a) iii) monthly adoption trend per team
team_monthly = (
    post
    .groupby(['team','month'])['used_ai_tool']
    .agg(total='count', ai='sum')
    .assign(adoption=lambda df: df['ai']/df['total']*100)
    .reset_index()
)
st.subheader("Teams: Month-over-Month Adoption Trends")
line = (
    alt.Chart(team_monthly)
    .mark_line(point=True)
    .encode(
        x=alt.X('month:T', title='Month'),
        y=alt.Y('adoption:Q', title='Adoption Rate (%)'),
        color='team:N',
        tooltip=['team','month', alt.Tooltip('adoption:Q', format='.1f')]
    )
    .properties(height=300)
)

# plot adoption rates
st.altair_chart(line, use_container_width=True)

# a) iii) teams flat or declining
st.subheader("📈 Adoption Change KPIs by Team")
ums_monthly = team_monthly.copy()
ums_monthly['month'] = ums_monthly['month'].dt.to_timestamp()
records = []
start, end = pd.Timestamp('2025-01-01'), pd.Timestamp('2025-04-01')
for team, grp in ums_monthly.groupby('team'):
    grp = grp.set_index('month').sort_index()
    jan = grp.at[start, 'adoption']
    feb = grp.at[pd.Timestamp('2025-02-01'), 'adoption']
    mar = grp.at[pd.Timestamp('2025-03-01'), 'adoption']
    apr = grp.at[end,   'adoption']
    records.append({
        'team':              team,
        'Jan_rate':          jan,
        'Feb_rate':          feb,
        'Mar_rate':          mar,
        'Apr_rate':          apr,
        'Δ abs % (Apr–Jan)': apr - jan,
        'Avg MoM abs %':     np.mean([feb - jan, mar - feb, apr - mar]),
    })
trend = pd.DataFrame(records)
st.dataframe(
    trend.style.format({
        'Jan_rate':'{:.1f}%','Feb_rate':'{:.1f}%','Mar_rate':'{:.1f}%','Apr_rate':'{:.1f}%',
        'Δ abs % (Apr–Jan)':'{:+.1f}%','Avg MoM abs %':'{:+.1f}%'
    }),
    use_container_width=True
)

# a) iii) identify users with stagnant/declining usage
st.subheader("Users: Monthly Adoption Δ-Metrics (Jan–Apr 2025)")
ums = pd.read_csv('data/user_monthly_summary.csv', parse_dates=['month'])
ums = ums[(ums['month']>=pd.Timestamp('2025-01-01')) & 
          (ums['month']<=pd.Timestamp('2025-04-01'))]

user_rates = (
    ums
    .pivot_table(
        index=['user_id','full_name','team'],
        columns='month',
        values='adoption_rate'
    )
    .reset_index()
)
user_rates.rename(columns={
    pd.Timestamp('2025-01-01'): 'Jan %',
    pd.Timestamp('2025-02-01'): 'Feb %',
    pd.Timestamp('2025-03-01'): 'Mar %',
    pd.Timestamp('2025-04-01'): 'Apr %'
}, inplace=True)

user_rates['Δ abs % (Apr–Jan)'] = user_rates['Apr %'] - user_rates['Jan %']

def avg_abs(vals):
    arr = [v for v in vals if pd.notna(v)]
    return np.mean(np.diff(arr)) if len(arr)>1 else np.nan

user_rates['Avg MoM abs %'] = user_rates.apply(lambda r:
    avg_abs([r[c] for c in ['Jan %','Feb %','Mar %','Apr %']]), axis=1)

user_rates['Δ rel % (Apr–Jan)'] = (
    (user_rates['Apr %'] - user_rates['Jan %']) /
    user_rates['Jan %'] * 100
).replace([np.inf,-np.inf], np.nan)

def avg_rel(vals):
    arr = [v for v in vals if pd.notna(v)]
    rel = [(arr[i] - arr[i-1]) / arr[i-1] * 100
           for i in range(1, len(arr)) if arr[i-1]!=0]
    return np.mean(rel) if rel else np.nan

user_rates['Avg MoM rel %'] = user_rates.apply(lambda r:
    avg_rel([r[c] for c in ['Jan %','Feb %','Mar %','Apr %']]), axis=1)

user_rates['n_months'] = user_rates[['Jan %','Feb %','Mar %','Apr %']].notna().sum(axis=1)
user_rates['decline_count'] = user_rates.apply(lambda r:
    int(sum(1 for d in np.diff(
        [r[c] for c in ['Jan %','Feb %','Mar %','Apr %'] if pd.notna(r[c])]
    ) if d<0)), axis=1)

def status(r):
    if r.n_months < 2:
        return 'Not enough data'
    arr = [r[c] for c in ['Jan %','Feb %','Mar %','Apr %'] if pd.notna(r[c])]
    if all(x == 100 for x in arr):
        return 'Full Adopter'
    if r['Avg MoM abs %'] > 0:
        return 'Growing'
    return 'Stagnant/Declining'

user_rates['Status'] = user_rates.apply(status, axis=1)

fmt = {
    'Jan %':'{:.1f}%','Feb %':'{:.1f}%','Mar %':'{:.1f}%','Apr %':'{:.1f}%',
    'Δ abs % (Apr–Jan)':'{:+.1f}%','Avg MoM abs %':'{:+.1f}%',
    'Δ rel % (Apr–Jan)':'{:+.1f}%','Avg MoM rel %':'{:+.1f}%',
    'decline_count':'{:.0f}'
}
st.dataframe(
    user_rates[
        ['user_id','full_name','team','Status','decline_count',
         'Jan %','Feb %','Mar %','Apr %',
         'Δ abs % (Apr–Jan)','Avg MoM abs %','Δ rel % (Apr–Jan)','Avg MoM rel %']
    ].style.format(fmt),
    height=400
)

base = (
    alt.Chart(user_rates)
    .mark_bar()
    .encode(
        x=alt.X(
            'full_name:N',
            sort=alt.SortField('user_id','ascending'),
            title='User'
        ),
        y=alt.Y('Avg MoM abs %:Q', title='Avg MoM abs %'),
        color=alt.Color(
            'Status:N',
            scale=alt.Scale(domain=['Growing','Not enough data','Full Adopter','Stagnant/Declining'],
                            range=['green','gray','blue','red'])
        ),
        tooltip=[
            'full_name','team',
            alt.Tooltip('Avg MoM abs %', format='+.1f', title='Avg MoM abs %'),
            alt.Tooltip('decline_count:Q', title='Decline Count'),
            'Status'
        ]
    )
)
dots = base.mark_point(filled=True, size=60).transform_filter(
    alt.datum['Avg MoM abs %'] == 0
)
full_dots = base.mark_point(filled=True, size=60, color='blue').transform_filter(
    (alt.datum['Status'] == 'Full Adopter') & (alt.datum['Avg MoM abs %'] == 0)
)

st.subheader("Users: Avg MoM abs % (Jan→Apr)")
st.altair_chart((base + dots + full_dots).properties(height=300), use_container_width=True)

st.subheader("Stagnant or Declining Users")
decliners = user_rates[user_rates['Status']=='Stagnant/Declining']
st.dataframe(
    decliners[['user_id','full_name','team','Avg MoM abs %','decline_count']]
    .style.format({'Avg MoM abs %': '{:+.1f}%','decline_count':'{:.0f}'}),
    height=250
)

def first_adoption_month(row):
    for m in ['Jan %','Feb %','Mar %','Apr %']:
        if pd.notna(row[m]) and row[m] > 0:
            return m
    return None

user_rates['first_month'] = user_rates.apply(first_adoption_month, axis=1)

def compute_since_metrics(row):
    order = ['Jan %','Feb %','Mar %','Apr %']
    if not row['first_month']:
        return pd.Series({
            'since_decline_count':   0,
            'since_increase_count':  1
        })
    idx = order.index(row['first_month'])
    seq = [row[m] for m in order[idx:] if pd.notna(row[m])]
    declines   = sum(1 for d in np.diff(seq) if d < 0)
    increases  = sum(1 for d in np.diff(seq) if d > 0) + 1
    return pd.Series({
        'since_decline_count':   declines,
        'since_increase_count':  increases
    })

since_metrics = user_rates.apply(compute_since_metrics, axis=1)
user_rates = pd.concat([user_rates, since_metrics], axis=1)

st.subheader("Consecutively Declining Users Only Since First Month of Adoption")
decline_since = user_rates[
    user_rates['since_decline_count'] > user_rates['since_increase_count']
]
st.dataframe(
    decline_since[
        ['user_id','full_name','team','first_month',
         'since_decline_count','since_increase_count','Avg MoM abs %']
    ].style.format({
        'since_decline_count':     '{:.0f}',
        'since_increase_count':    '{:.0f}',
        'Avg MoM abs %':           '{:+.1f}%'
    }),
    height=300
)

st.subheader("Consecutively Stagnant Users")
mask_months = user_rates[['Jan %','Feb %','Mar %','Apr %']].notna().sum(axis=1) >= 2
mask_zero = user_rates[['Jan %','Feb %','Mar %','Apr %']].fillna(0).eq(0).all(axis=1)
stagnant_users = user_rates[mask_months & mask_zero]
st.dataframe(
    stagnant_users[['user_id','full_name','team','n_months','Jan %','Feb %','Mar %','Apr %']]
    .style.format({
        'Jan %':'{:.1f}%', 'Feb %':'{:.1f}%', 'Mar %':'{:.1f}%', 'Apr %':'{:.1f}%'
    }),
    height=300
)
