import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

st.set_page_config(page_title="AI Efficiency Gains Dashboard", layout="wide")
st.title("⚡ AI Efficiency Gains by Task & Team")

# load directories and logs
df_ai = pd.read_csv('data/ai_usage_logs.csv', parse_dates=['date'])
df_manual = pd.read_csv('data/manual_task_logs.csv', parse_dates=['date'])

# tag AI logs method and select cols
df_ai['method'] = np.where(df_ai['used_ai_tool'], 'AI', 'Manual')
df_ai = df_ai[['user_id','team','task_type','date','task_duration_minutes','method']]

# derive team for manual entries
df_team_map = df_ai.groupby('user_id')['team'].first().reset_index()
df_manual = (
    df_manual.merge(df_team_map, on='user_id', how='left')
             .assign(method='Manual')
)
df_manual = df_manual[['user_id','team','task_type','date','task_duration_minutes','method']]

# combine data and extract month
all_data = pd.concat([df_ai, df_manual], ignore_index=True)
all_data['month'] = all_data['date'].dt.to_period('M')

# b) i) average durations by team & task type
teams = all_data['team'].dropna().unique()
for team in teams:
    st.header(f"Average Task Durations for {team}")
    avg_table = (
        all_data[all_data['team']==team]
        .groupby(['task_type','method'])['task_duration_minutes']
        .mean()
        .unstack(fill_value=np.nan)
        .rename(columns={'AI':'avg_dur_ai','Manual':'avg_dur_manual'})
        .reset_index()
    )
    st.dataframe(
        avg_table.style.format({'avg_dur_ai':'{:.1f}','avg_dur_manual':'{:.1f}'}),
        use_container_width=True
    )

# b) ii) percentage time saved by AI usage
st.header("Percentage Time Saved by AI Usage by Team & Task Type")
percent_frames = []
for team in teams:
    df_team = all_data[all_data['team']==team]
    pivot = df_team.pivot_table(
        index='task_type', columns='method', values='task_duration_minutes',
        aggfunc='mean', fill_value=np.nan
    )
    # ensure both columns exist
    pivot['Manual'] = pivot.get('Manual', np.nan)
    pivot['AI'] = pivot.get('AI', np.nan)
    pivot['pct_time_saved'] = (pivot['Manual'] - pivot['AI']) / pivot['Manual'] * 100
    temp = pivot.reset_index()[['task_type','pct_time_saved']]
    temp['team'] = team
    percent_frames.append(temp)
percent_df = pd.concat(percent_frames, ignore_index=True)
st.dataframe(
    percent_df.style.format({'pct_time_saved':'{:.1f}%'}), use_container_width=True
)


st.subheader("Overall Percentage Time Saved by AI Usage by Task Type")
overall_pivot = all_data.pivot_table(
    index='task_type',
    columns='method',
    values='task_duration_minutes',
    aggfunc='mean',
    fill_value=np.nan
)

overall_pivot['Manual'] = overall_pivot.get('Manual', np.nan)
overall_pivot['AI'] = overall_pivot.get('AI', np.nan)

overall_pivot['pct_time_saved'] = (overall_pivot['Manual'] - overall_pivot['AI']) / overall_pivot['Manual'] * 100

overall_df = (
    overall_pivot
    .reset_index()[['task_type', 'pct_time_saved']]
)
st.dataframe(
    overall_df.style.format({'pct_time_saved':'{:.1f}%'}),
    use_container_width=True
)

# b) iii) task durations over time: separate AI & Manual tables per team
st.header("Task Duration Trends Over Time by Month")
for team in teams:
    st.subheader(f"{team}: AI Durations by Month")
    ai_pivot = (
        all_data[(all_data['team']==team)&(all_data['method']=='AI')]
        .pivot_table(
            index='task_type', columns='month', values='task_duration_minutes', aggfunc='mean', fill_value=np.nan
        )
        .reset_index()
    )
    st.dataframe(
        ai_pivot.style.format({col:'{:.1f}' for col in ai_pivot.columns if col!='task_type'}),
        use_container_width=True
    )
    st.subheader(f"{team}: Manual Durations by Month")
    manual_pivot = (
        all_data[(all_data['team']==team)&(all_data['method']=='Manual')]
        .pivot_table(
            index='task_type', columns='month', values='task_duration_minutes', aggfunc='mean', fill_value=np.nan
        )
        .reset_index()
    )
    st.dataframe(
        manual_pivot.style.format({col:'{:.1f}' for col in manual_pivot.columns if col!='task_type'}),
        use_container_width=True
    )

# b) iv) total minutes per task per month (AI vs Manual)
st.header("Total Task Minutes by Month and Method")
for team in teams:
    st.subheader(f"{team}: Total Minutes by Month - AI")
    total_ai = (
        all_data[(all_data['team']==team)&(all_data['method']=='AI')]
        .groupby(['task_type','month'])['task_duration_minutes']
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )
    st.dataframe(
        total_ai.style.format({col:'{:.0f}' for col in total_ai.columns if col!='task_type'}),
        use_container_width=True
    )
    st.subheader(f"{team}: Total Minutes by Month - Manual")
    total_manual = (
        all_data[(all_data['team']==team)&(all_data['method']=='Manual')]
        .groupby(['task_type','month'])['task_duration_minutes']
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )
    st.dataframe(
        total_manual.style.format({col:'{:.0f}' for col in total_manual.columns if col!='task_type'}),
        use_container_width=True
    )

st.subheader("All Teams: Total Minutes by Month - AI")
overall_total_ai = (
    all_data[all_data['method']=='AI']
    .groupby(['task_type','month'])['task_duration_minutes']
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)
st.dataframe(
    overall_total_ai.style.format({col:'{:.0f}' for col in overall_total_ai.columns if col!='task_type'}),
    use_container_width=True
)

st.subheader("All Teams: Total Minutes by Month - Manual")
overall_total_manual = (
    all_data[all_data['method']=='Manual']
    .groupby(['task_type','month'])['task_duration_minutes']
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)
st.dataframe(
    overall_total_manual.style.format({col:'{:.0f}' for col in overall_total_manual.columns if col!='task_type'}),
    use_container_width=True
)

st.subheader("All Teams: Average Minutes per Task by Month - AI")
overall_avg_ai = (
    all_data[all_data['method']=='AI']
    .groupby(['task_type','month'])['task_duration_minutes']
    .mean()
    .unstack(fill_value=0)
    .reset_index()
)
st.dataframe(
    overall_avg_ai.style.format({col:'{:.1f}' for col in overall_avg_ai.columns if col!='task_type'}),
    use_container_width=True
)

st.subheader("All Teams: Average Minutes per Task by Month - Manual")
overall_avg_manual = (
    all_data[all_data['method']=='Manual']
    .groupby(['task_type','month'])['task_duration_minutes']
    .mean()
    .unstack(fill_value=0)
    .reset_index()
)
st.dataframe(
    overall_avg_manual.style.format({col:'{:.1f}' for col in overall_avg_manual.columns if col!='task_type'}),
    use_container_width=True
)

# b) v) average total task time per month pre- and post-AI introduction
st.header("Average Total Task Time per Month: Pre vs Post AI Introduction")

# pre-AI (manual only: Oct & Nov 2024)
pre = df_manual.copy()
pre['month'] = pre['date'].dt.to_period('M')
pre = pre[pre['month'].isin([pd.Period('2024-10'), pd.Period('2024-11')])]
pre_pivot = (
    pre.groupby(['task_type','month'])['task_duration_minutes']
       .sum()
       .unstack(fill_value=0)
       .reset_index()
)
st.subheader("Pre-AI (Manual Only): Oct & Nov 2024")
st.dataframe(
    pre_pivot.style.format({col:'{:.0f}' for col in pre_pivot.columns if col!='task_type'}),
    use_container_width=True
)

# post-AI (combined AI & Manual: Jan–Apr 2025)
post = all_data.copy()
post = post[post['month'].isin([pd.Period('2025-01'), pd.Period('2025-02'), pd.Period('2025-03'), pd.Period('2025-04')])]
post_pivot = (
    post.groupby(['task_type','month'])['task_duration_minutes']
        .sum()
        .unstack(fill_value=0)
        .reset_index()
)
st.subheader("Post-AI (All Methods): Jan–Apr 2025")
st.dataframe(
    post_pivot.style.format({col:'{:.0f}' for col in post_pivot.columns if col!='task_type'}),
    use_container_width=True
)

# b) vi) bar chart of percent saved
chart = alt.Chart(percent_df).mark_bar().encode(
    x=alt.X('pct_time_saved:Q', title='Time Saved (%)'),
    y=alt.Y('task_type:N', sort='-x', title='Task Type'),
    color='team:N',
    tooltip=['team','task_type', alt.Tooltip('pct_time_saved:Q', format='.1f', title='% Saved')]
).properties(height=400)
st.subheader("Time Saved (%) by Task Type & Team")
st.altair_chart(chart, use_container_width=True)
