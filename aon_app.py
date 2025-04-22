import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def main():
    st.title("Activity on Node (AON) Diagram Generator")

    if 'activities' not in st.session_state:
        st.session_state.activities = []
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = True

    if st.button("🔄 Reset All Inputs"):
        st.session_state.activities = []
        st.session_state.edit_mode = True
        st.experimental_rerun()

    if st.button("✏️ Edit Input Data"):
        st.session_state.edit_mode = True
        st.experimental_rerun()

    if st.session_state.edit_mode:
        num_activities = st.number_input("How many activities?", min_value=1, max_value=50, step=1, key='num_activities')
        activities = []

        for i in range(num_activities):
            with st.expander(f"Activity {i + 1}"):
                activity = st.text_input(f"Activity ID for Activity {i + 1}", key=f"id_{i}")
                duration = st.number_input(f"Duration for {activity}", min_value=1, step=1, key=f"duration_{i}")
                preds = st.text_input(f"Predecessors for {activity} (comma separated, leave blank if none)", key=f"pred_{i}")
                pred_list = [p.strip() for p in preds.split(',') if p.strip()]
                activities.append({'Activity': activity, 'Duration': duration, 'Predecessor': pred_list})

        if st.button("Generate AON Diagram"):
            st.session_state.activities = activities
            st.session_state.edit_mode = False
            st.experimental_rerun()

    else:
        df = pd.DataFrame(st.session_state.activities)
        df['EST'] = 0
        df['EFT'] = 0
        df['LST'] = 0
        df['LFT'] = 0

        for i, row in df.iterrows():
            preds = row['Predecessor']
            est = 0 if not preds else max(df.loc[df['Activity'].isin(preds), 'EFT'])
            eft = est + row['Duration']
            df.at[i, 'EST'] = est
            df.at[i, 'EFT'] = eft

        max_eft = df['EFT'].max()
        for activity in reversed(df['Activity'].tolist()):
            succs = df[df['Predecessor'].apply(lambda x: activity in x)]['Activity']
            lft = max_eft if succs.empty else min(df.loc[df['Activity'].isin(succs), 'LST'])
            duration = df.loc[df['Activity'] == activity, 'Duration'].values[0]
            lst = lft - duration
            df.loc[df['Activity'] == activity, ['LST', 'LFT']] = [lst, lft]

        df['Float'] = df['LST'] - df['EST']
        df['Critical'] = df['Float'] == 0

        critical_activities = df[df['Critical']].sort_values(by='EST')
        critical_path = ' → '.join(critical_activities['Activity'])
        project_duration = df['EFT'].max()

        st.subheader("Calculated Table")
        st.dataframe(df)

        st.success(f"📌 Critical Path: {critical_path}")
        st.info(f"🕒 Total Project Duration: {project_duration} days")

        # Layout management to avoid overlapping arrows and nodes
        fig, ax = plt.subplots(figsize=(14, 10))
        pos = {}
        layer_map = df.groupby('EST')['Activity'].apply(list).to_dict()
        for layer_idx, (est, activities) in enumerate(sorted(layer_map.items())):
            for act_idx, act in enumerate(sorted(activities)):
                pos[act] = (layer_idx * 7, -act_idx * 6)

        node_width, node_height = 4, 3
        for _, row in df.iterrows():
            x, y = pos[row['Activity']]
            rect_color = 'red' if row['Critical'] else 'lightblue'
            rect = Rectangle((x - node_width / 2, y - node_height / 2), node_width, node_height,
                             linewidth=1, edgecolor='black', facecolor=rect_color)
            ax.add_patch(rect)
            ax.text(x - node_width/2 + 0.2, y + node_height/2 - 0.6, f"{row['EST']}", fontsize=7)
            ax.text(x + node_width/2 - 0.8, y + node_height/2 - 0.6, f"{row['EFT']}", fontsize=7)
            ax.text(x - node_width/2 + 0.2, y - node_height/2 + 0.1, f"{row['LST']}", fontsize=7)
            ax.text(x + node_width/2 - 0.8, y - node_height/2 + 0.1, f"{row['LFT']}", fontsize=7)
            ax.text(x, y, f"{row['Activity']} ({row['Duration']})", fontsize=11, ha='center', va='center', fontweight='bold')

        for _, row in df.iterrows():
            for pred in row['Predecessor']:
                if pred in pos:
                    x1, y1 = pos[pred]
                    x2, y2 = pos[row['Activity']]
                    dx = node_width / 2
                    ax.annotate('', xy=(x2 - dx, y2), xytext=(x1 + dx, y1),
                                arrowprops=dict(arrowstyle='->', lw=1.5))

        ax.set_xlim(-5, max(x for x, _ in pos.values()) + 10)
        ax.set_ylim(min(y for _, y in pos.values()) - 6, 5)
        ax.set_aspect('equal')
        ax.axis('off')
        st.pyplot(fig)

if __name__ == '__main__':
    main()