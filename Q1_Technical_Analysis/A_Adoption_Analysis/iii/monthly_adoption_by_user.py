# monthly_adoption_by_user_streamlit.py
# Streamlit app: Monthly Adoption Rates & Δ‐Metrics by Individual User

import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

# 1. Load user×month summary
ums = pd.read_csv('data/user_monthly_summary.csv', parse_dates=['month'])

# 2. Restrict to 2025‐01 through 2025‐04 (ignore partial May)
start = pd.Timestamp('2025-01-01')
end   = pd.Timestamp('2025-04-01')
ums   = ums[(ums['month'] >= start) & (ums['month'] <= end)]

# 3. Pivot to get one row per user with Jan–Apr adoption rates
user_rates = (
    ums
    .pivot_table(
        index=['user_id','full_name'],
        columns='month',
        values='adoption_rate'
    )
    .reset_index()
)
# rename month columns to friendly labels
month_map = {
    pd.Timestamp('2025-01-01'): 'Jan %',
    pd.Timestamp('2025-02-01'): 'Feb %',
    pd.Timestamp('2025-03-01'): 'Mar %',
    pd.Timestamp('2025-04-01'): 'Apr %'
}
user_rates = user_rates.rename(columns=month_map)

# 4. Compute Δ‐metrics

# 4a) Absolute difference Apr – Jan
user_rates['Δ abs % (Apr–Jan)'] = user_rates['Apr %'] - user_rates['Jan %']

# 4b) Avg MoM absolute change (ignore missing months)
def avg_abs_deltas(row):
    vals = [row[m] for m in ['Jan %','Feb %','Mar %','Apr %'] if pd.notnull(row.get(m))]
    if len(vals) < 2:
        return np.nan
    deltas = [vals[i] - vals[i-1] for i in range(1, len(vals))]
    return sum(deltas) / len(deltas)

user_rates['Avg MoM abs %'] = user_rates.apply(avg_abs_deltas, axis=1)

# 4c) Relative % change Apr vs Jan
user_rates['Δ rel % (Apr–Jan)'] = (
    (user_rates['Apr %'] - user_rates['Jan %']) /
    user_rates['Jan %'] * 100
).replace([np.inf, -np.inf], np.nan)

# 4d) Avg MoM relative % change (ignore missing months)
def avg_rel_deltas(row):
    vals = [row[m] for m in ['Jan %','Feb %','Mar %','Apr %'] if pd.notnull(row.get(m))]
    rels = []
    for i in range(1, len(vals)):
        prev, curr = vals[i-1], vals[i]
        if prev != 0:
            rels.append((curr - prev) / prev * 100)
    return sum(rels) / len(rels) if rels else np.nan

user_rates['Avg MoM rel %'] = user_rates.apply(avg_rel_deltas, axis=1)

# 5. Determine number of months present
user_rates['n_months'] = user_rates[['Jan %','Feb %','Mar %','Apr %']].notna().sum(axis=1)

# 6. Count declining months (negative abs delta)
def count_declines(row):
    vals = [row[m] for m in ['Jan %','Feb %','Mar %','Apr %'] if pd.notnull(row.get(m))]
    deltas = [vals[i] - vals[i-1] for i in range(1, len(vals))]
    return sum(1 for d in deltas if d < 0)

user_rates['decline_count'] = user_rates.apply(count_declines, axis=1)

# 7. Flag status
#  - Not enough data if <2 months
#  - Full Adopter if all non-null rates ==100
#  - Stagnant/Declining if decline_count>0
#  - Growing otherwise
def compute_status(row):
    if row['n_months'] < 2:
        return 'Not enough data'
    # check all non-null months == 100
    rates = [row[m] for m in ['Jan %','Feb %','Mar %','Apr %'] if pd.notnull(row.get(m))]
    if all(r == 100 for r in rates):
        return 'Full Adopter'
    if row['decline_count'] > 0:
        return 'Stagnant/Declining'
    return 'Growing'

user_rates['overall status'] = user_rates.apply(compute_status, axis=1)

# 8. Build severity label for coloring
def severity_label(row):
    if row['overall status'] == 'Stagnant/Declining':
        return f"Decline {int(row['decline_count'])} mo"
    return row['overall status']

user_rates['severity'] = user_rates.apply(severity_label, axis=1)

# 9. Streamlit UI
st.set_page_config(page_title="User Adoption Δ‐Metrics", layout="wide")
st.title("📊 User Adoption Change KPIs (Jan–Apr 2025)")

# show full table
fmt = {
    'Jan %':             '{:.1f}%'.format,
    'Feb %':             '{:.1f}%'.format,
    'Mar %':             '{:.1f}%'.format,
    'Apr %':             '{:.1f}%'.format,
    'Δ abs % (Apr–Jan)': '{:+.1f}%'.format,
    'Avg MoM abs %':     '{:+.1f}%'.format,
    'Δ rel % (Apr–Jan)': '{:+.1f}%'.format,
    'Avg MoM rel %':     '{:+.1f}%'.format,
    'decline_count':     '{:.0f}'.format,
}
st.dataframe(
    user_rates[
        ['user_id','full_name','overall status','decline_count','Jan %','Feb %','Mar %','Apr %',
         'Δ abs % (Apr–Jan)','Avg MoM abs %','Δ rel % (Apr–Jan)','Avg MoM rel %']
    ]
    .style.format(fmt)
)

# 10. Highlight in bar chart with severity colors
color_domain = [
    'Growing',
    'Not enough data',
    'Full Adopter',
    'Decline 1 mo',
    'Decline 2 mo',
    'Decline 3 mo'
]
color_range = ['green','gray','blue','yellow','orange','red']

chart = (
    alt.Chart(user_rates)
    .mark_bar()
    .encode(
        x=alt.X('full_name:N', sort='-y', title='User'),
        y=alt.Y('Δ abs % (Apr–Jan):Q', title='Absolute Change (Apr vs Jan) %'),
        color=alt.Color(
            'severity:N',
            scale=alt.Scale(domain=color_domain, range=color_range),
            legend=alt.Legend(title='Status / Severity')
        ),
        tooltip=[
            'full_name',
            alt.Tooltip('Jan %', format='.1f'),
            alt.Tooltip('Apr %', format='.1f'),
            alt.Tooltip('decline_count:Q', title='Decline Count'),
            alt.Tooltip('Δ abs % (Apr–Jan):Q', format='+.1f'),
            'overall status'
        ]
    )
)
st.subheader("Users: Absolute Adoption Δ (Apr vs Jan)")
st.altair_chart(chart, use_container_width=True)
