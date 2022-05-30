# adoption_analysis1.py
# Streamlit app: AI Adoption Dashboard with full Q1/Q2/Q3 + per‐user Δ‐metrics

import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

# — App Config
st.set_page_config(page_title="AI Adoption Dashboard", layout="wide")
st.title("🚀 AI Tool Adoption & Efficiency Dashboard")

# — Load & Combine Logs
users       = pd.read_csv('data/user_directory.csv', parse_dates=['join_date'])
ai_logs     = pd.read_csv('data/ai_usage_logs.csv',    parse_dates=['date'])
manual_logs = pd.read_csv('data/manual_task_logs.csv', parse_dates=['date'])

# derive each user's primary team from AI logs
user_team_map = (
    ai_logs
    .groupby('user_id')['team']
    .agg(lambda s: s.mode().iloc[0])
    .reset_index()
)

# tag manual logs as non-AI, merge team
manual = (
    manual_logs
    .merge(user_team_map, on='user_id', how='inner')
    .assign(used_ai_tool=False)
)

# stitch together AI+manual
data = pd.concat([
    ai_logs[['user_id','team','task_type','date','used_ai_tool']],
    manual[['user_id','team','task_type','date','used_ai_tool']]
], ignore_index=True)

# restrict to Jan–Apr 2025
post = data[(data['date'] >= '2025-01-01') & (data['date'] < '2025-05-01')].copy()
post['month'] = post['date'].dt.to_period('M')

# — Q1: What percentage of tasks used the AI tool, segmented by team?
st.header("· 1. What percentage of tasks used the AI tool, segmented by team?")

# overall per‐team×task_type adoption
overall_tt = (
    post
    .groupby(['team','task_type'])['used_ai_tool']
    .agg(total_tasks='count', ai_tasks='sum')
    .assign(overall_adoption_rate=lambda df: df['ai_tasks']/df['total_tasks']*100)
    .reset_index()
)

# grouped‐bar: X=team, offset=task_type, Y=adoption_rate
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
st.altair_chart(chart_tt, use_container_width=True)

# breakdown tables per team
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

# raw per‐team totals for summary lines
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

# — Q2: Which teams show the highest and lowest AI adoption rates?
st.header("· 2. Which teams show the highest and lowest AI adoption rates?")

adopt_team = (
    post
    .groupby('team')['used_ai_tool']
    .agg(total_tasks='count', ai_tasks='sum')
    .assign(adoption_rate=lambda df: df['ai_tasks']/df['total_tasks']*100)
    .reset_index()
)
high = adopt_team.loc[adopt_team['adoption_rate'].idxmax()]
low  = adopt_team.loc[adopt_team['adoption_rate'].idxmin()]

c1, c2 = st.columns(2)
c1.metric("🏆 Highest Adopting Team", high.team, f"{high.adoption_rate:.1f}%")
c2.metric("📉 Lowest Adopting Team",  low.team,  f"{low.adoption_rate:.1f}%")

# — Q3: Identify any users or teams exhibiting stagnant or declining AI usage
st.header("· 3. Identify any users or teams exhibiting stagnant or declining AI usage over time")

# 3a) Team month-over-month trends
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
st.altair_chart(line, use_container_width=True)

def avg_delta(s):
    return s.diff().mean() if len(s)>1 else 0

team_trends = (
    team_monthly
    .groupby('team')['adoption']
    .apply(avg_delta)
    .reset_index(name='avg_delta')
)
st.subheader("Teams with Stagnant/Declining Adoption (avg Δ ≤ 0)")
st.dataframe(
    team_trends[team_trends['avg_delta']<=0]
    .style.format({'avg_delta':'{:+.1f}%'}),
    height=120
)

# 3b) Users: Monthly Δ-Metrics & decline list
st.subheader("Users: Monthly Adoption Δ-Metrics (Jan-Apr 2025)")

# load user×month summary
ums = pd.read_csv('data/user_monthly_summary.csv', parse_dates=['month'])
ums = ums[(ums['month']>=pd.Timestamp('2025-01-01')) & 
          (ums['month']<=pd.Timestamp('2025-04-01'))]

# pivot one row per user
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

# compute Δ-metrics
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

# updated status logic: positive avg → Growing
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

# — Full user table
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

# — Refined user Δ-chart (Avg MoM abs % on Y), sorted by user_id
color_domain = ['Growing','Not enough data','Full Adopter','Stagnant/Declining']
color_range  = ['green','gray','blue','red']
chart_u = (
    alt.Chart(user_rates)
    .mark_bar()
    .encode(
        x=alt.X(
            'full_name:N',
            sort=alt.EncodingSortField(field='user_id', order='ascending'),
            title='User'
        ),
        y=alt.Y('Avg MoM abs %:Q', title='Avg MoM abs %'),
        color=alt.Color(
            'Status:N',
            scale=alt.Scale(domain=color_domain, range=color_range)
        ),
        tooltip=[
            'full_name','team',
            alt.Tooltip('Avg MoM abs %', format='+.1f', title='Avg MoM abs %'),
            alt.Tooltip('decline_count:Q', title='Decline Count'),
            'Status'
        ]
    )
    .properties(height=300)
)
st.subheader("Users: Avg MoM abs % (Jan→Apr)")
st.altair_chart(chart_u, use_container_width=True)

# — Stagnant/Declining Users Only
st.subheader("Stagnant or Declining Users Only")
decliners = user_rates[user_rates['Status']=='Stagnant/Declining']
st.dataframe(
    decliners[['user_id','full_name','team','Avg MoM abs %','decline_count']]
    .style.format({'Avg MoM abs %': '{:+.1f}%', 'decline_count':'{:.0f}'}),
    height=250
)
