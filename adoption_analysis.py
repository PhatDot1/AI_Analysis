# adoption_streamlit.py
# Streamlit app: Comprehensive AI adoption & usage analysis with manual logs integration
# + Pre-AI vs Jan–Apr 2025 monthly duration tables
# + Adoption tables now only consider Jan–Apr 2025

import pandas as pd
import streamlit as st

# Page config
st.set_page_config(page_title="AI Adoption Dashboard", layout="wide")

# -------------------
# Load data
# -------------------
users       = pd.read_csv('data/user_directory.csv',   parse_dates=['join_date'])
ai_logs     = pd.read_csv('data/ai_usage_logs.csv',    parse_dates=['date'])
manual_logs = pd.read_csv('data/manual_task_logs.csv', parse_dates=['date'])

# -------------------
# Combine AI + manual logs
# -------------------
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
    ai_logs[['user_id','team','task_type','date','used_ai_tool','task_duration_minutes']],
    manual[['user_id','team','task_type','date','used_ai_tool','task_duration_minutes']]
], ignore_index=True)
data['month'] = data['date'].dt.to_period('M')

# -------------------
# Split Pre-AI vs Post-AI
# -------------------
pre_ai  = data[data['date'] < '2025-01-01']
post_ai = data[(data['date'] >= '2025-01-01') & (data['date'] < '2025-05-01')]

pre_months  = sorted(pre_ai['month'].unique())
post_months = [
    pd.Period('2025-01','M'),
    pd.Period('2025-02','M'),
    pd.Period('2025-03','M'),
    pd.Period('2025-04','M'),
]

# -------------------
# Pre-AI: avg monthly task duration
# -------------------
# by Team
pre_team = (
    pre_ai
    .groupby(['team','month'])['task_duration_minutes']
    .mean()
    .unstack(fill_value=pd.NA)
)
pre_team['Pre Avg Dur'] = pre_team.mean(axis=1)
pre_team = pre_team.reset_index()
pre_team.columns = (
    ['team'] +
    [f"{m} avg dur (pre)" for m in pre_months] +
    ['Pre Avg Dur']
)

# by Task Type
pre_task = (
    pre_ai
    .groupby(['task_type','month'])['task_duration_minutes']
    .mean()
    .unstack(fill_value=pd.NA)
)
pre_task['Pre Avg Dur'] = pre_task.mean(axis=1)
pre_task = pre_task.reset_index()
pre_task.columns = (
    ['task_type'] +
    [f"{m} avg dur (pre)" for m in pre_months] +
    ['Pre Avg Dur']
)

# by Team & Task Type
pre_team_task = (
    pre_ai
    .groupby(['team','task_type','month'])['task_duration_minutes']
    .mean()
    .unstack(fill_value=pd.NA)
)
pre_team_task['Pre Avg Dur'] = pre_team_task.mean(axis=1)
pre_team_task = pre_team_task.reset_index()
pre_team_task.columns = (
    ['team','task_type'] +
    [f"{m} avg dur (pre)" for m in pre_months] +
    ['Pre Avg Dur']
)

# -------------------
# Post-AI (Jan–Apr 2025): avg monthly task duration
# -------------------
post_overall_dur = (
    post_ai
    .groupby('month')['task_duration_minutes']
    .mean()
    .reindex(post_months)
    .reset_index(name='avg_dur')
)
post_overall_dur['month'] = post_overall_dur['month'].astype(str)

post_team = (
    post_ai
    .groupby(['team','month'])['task_duration_minutes']
    .mean()
    .unstack(fill_value=pd.NA)
)
post_team['Post Avg Dur'] = post_team.mean(axis=1)
post_team = post_team.reset_index()
post_team.columns = (
    ['team'] +
    [f"{m} avg dur" for m in post_months] +
    ['Post Avg Dur']
)

post_task = (
    post_ai
    .groupby(['task_type','month'])['task_duration_minutes']
    .mean()
    .unstack(fill_value=pd.NA)
)
post_task['Post Avg Dur'] = post_task.mean(axis=1)
post_task = post_task.reset_index()
post_task.columns = (
    ['task_type'] +
    [f"{m} avg dur" for m in post_months] +
    ['Post Avg Dur']
)

post_team_task = (
    post_ai
    .groupby(['team','task_type','month'])['task_duration_minutes']
    .mean()
    .unstack(fill_value=pd.NA)
)
post_team_task['Post Avg Dur'] = post_team_task.mean(axis=1)
post_team_task = post_team_task.reset_index()
post_team_task.columns = (
    ['team','task_type'] +
    [f"{m} avg dur" for m in post_months] +
    ['Post Avg Dur']
)

# -------------------
# Streamlit UI: Durations tables
# -------------------
st.title("AI Adoption & Task Duration Dashboard")

st.header("Average Task Durations: Pre-AI vs Jan–Apr 2025")

st.subheader("By Team")
pre_post_team = pre_team.merge(post_team, on='team', how='outer')
team_cols = [c for c in pre_post_team.columns if c != 'team']
st.dataframe(pre_post_team.style.format({c: '{:.1f}' for c in team_cols}))

st.subheader("By Task Type")
pre_post_task = pre_task.merge(post_task, on='task_type', how='outer')
task_cols = [c for c in pre_post_task.columns if c != 'task_type']
st.dataframe(pre_post_task.style.format({c: '{:.1f}' for c in task_cols}))

st.subheader("By Team & Task Type")
pre_post_team_task = pre_team_task.merge(post_team_task, on=['team','task_type'], how='outer')
tt_cols = [c for c in pre_post_team_task.columns if c not in ('team','task_type')]
st.dataframe(pre_post_team_task.style.format({c: '{:.1f}' for c in tt_cols}))

# -------------------
# Adoption tables (only Jan–Apr 2025)
# -------------------

# Overall by Team
adopt_team = (
    post_ai
    .groupby('team')['used_ai_tool']
    .agg(total_tasks='count', ai_tasks='sum')
    .assign(adoption_rate=lambda df: df['ai_tasks']/df['total_tasks']*100)
    .reset_index()
)
st.header("Overall Adoption by Team (Jan–Apr 2025)")
st.dataframe(adopt_team.style.format({'adoption_rate':'{:.1f}%'}))

# Overall by Task Type
adopt_task = (
    post_ai
    .groupby('task_type')['used_ai_tool']
    .agg(total_tasks='count', ai_tasks='sum')
    .assign(adoption_rate=lambda df: df['ai_tasks']/df['total_tasks']*100)
    .reset_index()
)
st.header("Overall Adoption by Task Type (Jan–Apr 2025)")
st.dataframe(adopt_task.style.format({'adoption_rate':'{:.1f}%'}))

# Adoption by Team & Task Type (overall + monthly Jan–Apr)
overall_adopt_tt = (
    post_ai
    .groupby(['team','task_type'])['used_ai_tool']
    .agg(overall_total_tasks='count', overall_ai_tasks='sum')
    .assign(overall_adoption_rate=lambda df: df['overall_ai_tasks']/df['overall_total_tasks']*100)
    .reset_index()
)
monthly_adopt_tt = (
    post_ai
    .groupby(['team','task_type','month'])['used_ai_tool']
    .agg(total_tasks='count', ai_tasks='sum')
    .assign(adoption_rate=lambda df: df['ai_tasks']/df['total_tasks']*100)
    .reset_index()
)
monthly_pivot = (
    monthly_adopt_tt
    .pivot(index=['team','task_type'], columns='month', values='adoption_rate')
    .reindex(columns=post_months, fill_value=0)
    .reset_index()
)
monthly_pivot.columns = ['team','task_type'] + [f"{m} %" for m in post_months]
adopt_tt_full = overall_adopt_tt.merge(monthly_pivot, on=['team','task_type'], how='left')

st.header("Adoption by Team & Task Type (Jan–Apr 2025)")
fmt = {'overall_adoption_rate':'{:.1f}%'}
fmt.update({f"{m} %": '{:.1f}%' for m in post_months})
st.dataframe(adopt_tt_full.style.format(fmt))
