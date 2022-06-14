import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

# App Config
st.set_page_config(page_title="AI Quality Assessment Dashboard", layout="wide")
st.title("🤖 AI Quality Assessment & Trend Explorer")

# Load data
ai_logs = pd.read_csv('data/ai_usage_logs.csv', parse_dates=['date'])
users   = pd.read_csv('data/user_directory.csv', parse_dates=['join_date'])

# Prepare AI-used entries with accuracy
df = ai_logs[ai_logs['used_ai_tool'] & ai_logs['ai_prediction_accuracy'].notna()].copy()
df['month'] = df['date'].dt.to_period('M')

# Sidebar filters
st.sidebar.header("Filters")
team_sel  = st.sidebar.multiselect("Teams", df['team'].unique(), df['team'].unique())
task_sel  = st.sidebar.multiselect("Task Types", df['task_type'].unique(), df['task_type'].unique())
user_sel  = st.sidebar.multiselect("Users", df['user_id'].unique(), df['user_id'].unique())
month_sel = st.sidebar.multiselect("Months", df['month'].astype(str).unique(), df['month'].astype(str).unique())

df = df[
    df['team'].isin(team_sel) &
    df['task_type'].isin(task_sel) &
    df['user_id'].isin(user_sel) &
    df['month'].astype(str).isin(month_sel)
]

# Average AI prediction accuracy by task type
st.header("1. Avg AI Prediction Accuracy by Task & Team")
acc_tt = df.groupby(['team','task_type'])['ai_prediction_accuracy'].mean().reset_index()
st.dataframe(acc_tt.style.format({'ai_prediction_accuracy':'{:.2f}'}), use_container_width=True)

# Monthly Avg Accuracy pivot
st.header("2. Monthly Avg Prediction Accuracy by Team & Task")
acc_month = (
    df
    .groupby(['month','team','task_type'])['ai_prediction_accuracy']
    .mean()
    .unstack('month')
    .reset_index()
)
st.dataframe(
    acc_month.style.format(
        {col:'{:.2f}' for col in acc_month.columns if col not in ['team','task_type']}
    ),
    use_container_width=True
)

# ii. Outliers & concerning trends: predictions below 70%

# % Predictions <70%
st.header("3. % of Predictions < 70% Accuracy")
threshold   = 0.70
total_preds = len(df)
low_preds   = (df['ai_prediction_accuracy'] < threshold).sum()
st.markdown(f"**Overall:** {(low_preds/total_preds)*100:.1f}% below 70%")

st.subheader("By Team")
pct_team = (
    df
    .groupby('team')['ai_prediction_accuracy']
    .apply(lambda s: (s < threshold).mean() * 100)
    .reset_index(name='pct_below_70')
)
st.dataframe(pct_team.style.format({'pct_below_70':'{:.1f}%'}), use_container_width=True)

st.subheader("By Task")
pct_task = (
    df
    .groupby('task_type')['ai_prediction_accuracy']
    .apply(lambda s: (s < threshold).mean() * 100)
    .reset_index(name='pct_below_70')
)
st.dataframe(pct_task.style.format({'pct_below_70':'{:.1f}%'}), use_container_width=True)

st.subheader("By Team & Task")
tt = (
    df
    .groupby(['team','task_type'])['ai_prediction_accuracy']
    .apply(lambda s: (s < threshold).mean() * 100)
    .reset_index(name='pct_below_70')
)
st.dataframe(tt.style.format({'pct_below_70':'{:.1f}%'}), use_container_width=True)

# 4–6: Drill into low‐accuracy entries and distributions


# Accuracy distribution per task
st.header("4. Accuracy Distribution by Task")
for task in df['task_type'].unique():
    st.subheader(task)
    stats = df[df['task_type']==task]['ai_prediction_accuracy'].describe()
    st.write(stats.apply(lambda x: f"{x:.2f}"))

# AI Accuracy by User & Team
tie = df.merge(users[['user_id','full_name']], on='user_id', how='left')
st.header("5. AI Accuracy by User & Team")
usr_ac = tie.groupby(['user_id','full_name','team'])['ai_prediction_accuracy'].agg(['mean','count']).reset_index()
usr_ac.columns = ['user_id','full_name','team','avg_accuracy','n_predictions']
st.dataframe(usr_ac.style.format({'avg_accuracy':'{:.2f}'}), use_container_width=True)

# Low-accuracy entries
st.header("6. Entries with Accuracy < 70%")
low = tie[tie['ai_prediction_accuracy'] < threshold][
    ['user_id','full_name','team','task_type','date','ai_prediction_accuracy']
]
st.dataframe(low.style.format({'ai_prediction_accuracy':'{:.2f}'}), use_container_width=True)

# Adoption Rate vs. Prediction Accuracy (Overall)
st.header("7. Adoption Rate vs. Prediction Accuracy")
df_adopt    = ai_logs.groupby(['team','user_id'])['used_ai_tool'].mean().reset_index(name='user_adoption_rate')
df_acc_user = df.groupby('user_id')['ai_prediction_accuracy'].mean().reset_index(name='user_avg_accuracy')
df_user     = df_adopt.merge(df_acc_user, on='user_id')

chart_scatter = alt.Chart(df_user).mark_circle(size=60).encode(
    x=alt.X('user_adoption_rate:Q', title='User Adoption Rate'),
    y=alt.Y('user_avg_accuracy:Q', title='User Avg Prediction Accuracy',
            scale=alt.Scale(domain=[0.56, 1.0])),
    color='team:N',
    tooltip=['user_id','team',
             alt.Tooltip('user_adoption_rate:Q', format='.2f'),
             alt.Tooltip('user_avg_accuracy:Q', format='.2f')]
)
reg_line = chart_scatter.transform_regression(
    'user_adoption_rate','user_avg_accuracy',groupby=['team']
).mark_line()
st.altair_chart(chart_scatter + reg_line, use_container_width=True)

# Compute and show slopes for Chart 7
slopes7 = (
    df_user
    .groupby('team')
    .apply(lambda g: np.polyfit(g['user_adoption_rate'], g['user_avg_accuracy'], 1)[0])
    .reset_index(name='slope_adopt_to_acc')
)
st.subheader("7️⃣ Regression Slopes by Team (Adoption → Accuracy)")
st.dataframe(slopes7.style.format({'slope_adopt_to_acc':'{:.3f}'}), use_container_width=True)

# Avg Task Duration vs. Avg Prediction Accuracy (Overall)
st.header("8. Avg Task Duration vs. Avg Prediction Accuracy")
user_dur  = df.groupby('user_id')['task_duration_minutes'].mean().reset_index(name='user_avg_duration')
df_user2  = user_dur.merge(df_acc_user, on='user_id').merge(df_adopt[['user_id','team']], on='user_id')

chart_scatter2 = alt.Chart(df_user2).mark_circle(size=60).encode(
    x=alt.X('user_avg_accuracy:Q', title='User Avg Prediction Accuracy',
            scale=alt.Scale(domain=[0.56, 1.0])),
    y=alt.Y('user_avg_duration:Q', title='User Avg Task Duration (min)'),
    color='team:N',
    tooltip=['user_id','team',
             alt.Tooltip('user_avg_accuracy:Q', format='.2f'),
             alt.Tooltip('user_avg_duration:Q', format='.1f')]
)
reg_line2 = chart_scatter2.transform_regression(
    'user_avg_accuracy','user_avg_duration',groupby=['team']
).mark_line()
st.altair_chart(chart_scatter2 + reg_line2, use_container_width=True)

# Compute and show slopes for Chart 8
slopes8 = (
    df_user2
    .groupby('team')
    .apply(lambda g: np.polyfit(g['user_avg_accuracy'], g['user_avg_duration'], 1)[0])
    .reset_index(name='slope_acc_to_dur')
)
st.subheader("8️⃣ Regression Slopes by Team (Accuracy → Duration)")
st.dataframe(slopes8.style.format({'slope_acc_to_dur':'{:.3f}'}), use_container_width=True)

# Prediction Accuracy Over Time by Team
st.header("9. Prediction Accuracy Over Time by Team")
team_trend = df.groupby(['month','team'])['ai_prediction_accuracy'].mean().reset_index()
acc_team_line = alt.Chart(team_trend).mark_line(point=True).encode(
    x='month:T',
    y=alt.Y('ai_prediction_accuracy:Q', title='Avg Accuracy'),
    color='team:N',
    tooltip=['month','team', alt.Tooltip('ai_prediction_accuracy:Q', format='.2f')]
).properties(height=300)
st.altair_chart(acc_team_line, use_container_width=True)

# Prediction Accuracy Over Time by Task Type
st.header("10. Prediction Accuracy Over Time by Task Type")
task_trend = df.groupby(['month','task_type'])['ai_prediction_accuracy'].mean().reset_index()
acc_task_line = alt.Chart(task_trend).mark_line(point=True).encode(
    x='month:T',
    y='ai_prediction_accuracy:Q',
    color='task_type:N',
    tooltip=['month','task_type', alt.Tooltip('ai_prediction_accuracy:Q', format='.2f')]
).properties(height=300)
st.altair_chart(acc_task_line, use_container_width=True)

# Prediction Accuracy Over Time by Team & Task Type
st.header("11. Prediction Accuracy Over Time by Team & Task Type")
tt_trend = df.groupby(['month','team','task_type'])['ai_prediction_accuracy'].mean().reset_index()
acc_tt_line = alt.Chart(tt_trend).mark_line(point=True).encode(
    x='month:T',
    y='ai_prediction_accuracy:Q',
    color='team:N',
    strokeDash='task_type:N',
    tooltip=['month','team','task_type', alt.Tooltip('ai_prediction_accuracy:Q', format='.2f')]
).properties(height=300)
st.altair_chart(acc_tt_line, use_container_width=True)

# 12. Accuracy vs. Duration Scatter by Team & Task
st.header("12. Accuracy vs. Duration Scatter by Team & Task")
for team in df['team'].unique():
    for task in df['task_type'].unique():
        sub = df[(df['team'] == team) & (df['task_type'] == task)]
        if not sub.empty:
            st.subheader(f"{team} – {task}")
            base = alt.Chart(sub).encode(
                x=alt.X('task_duration_minutes:Q', title='Task Duration (min)'),
                y=alt.Y('ai_prediction_accuracy:Q', title='AI Prediction Accuracy',
                        scale=alt.Scale(domain=[0.56, 1.0])),
                tooltip=[
                    'user_id', 'date',
                    alt.Tooltip('task_duration_minutes:Q', format='.1f'),
                    alt.Tooltip('ai_prediction_accuracy:Q', format='.2f')
                ]
            )
            scatter = base.mark_circle(size=60)
            # regression line: Accuracy ~ Duration
            reg_line = base.transform_regression(
                'task_duration_minutes',
                'ai_prediction_accuracy',
                groupby=['team','task_type']
            ).mark_line(color='firebrick')
            st.altair_chart((scatter + reg_line).properties(height=200, width=400), use_container_width=True)

# compute & show slopes for this section (acc per min of duration)
st.header("🔢 Regression Slopes by Team & Task (Accuracy → Duration)")
slopes12 = (
    df
    .groupby(['team','task_type'])
    .apply(lambda g: np.polyfit(
        g['task_duration_minutes'],
        g['ai_prediction_accuracy'],
        1
    )[0])
    .reset_index(name='slope_acc_per_min')
)
# 'slope_acc_per_min' is Δ accuracy (in decimal) per 1 minute of duration
st.dataframe(
    slopes12.style.format({'slope_acc_per_min':'{:.4f}'}),
    use_container_width=True
)


# footer note
st.markdown("---")
st.markdown("*Use filters to refine your view.*")
