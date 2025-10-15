"""
Exercise 4: Streamlit Community Cloud Deployment
A simplified version of the dashboard designed for cloud deployment
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path

# Database path - for cloud deployment, the db file should be in the same directory
DB_PATH = Path(__file__).parent / "speakger.db"


@st.cache_resource
def get_connection():
    """Create database connection (cached)"""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data(ttl=600)
def get_random_speech():
    """Get a random speech from the database"""
    conn = get_connection()
    query = """
        SELECT
            s.Date,
            s.Party,
            s.Speech,
            m.Name,
            m.SexOrGender
        FROM speeches s
        LEFT JOIN mps_meta m ON s.MPID = m.MPID
        WHERE LENGTH(s.Speech) > 100
        ORDER BY RANDOM()
        LIMIT 1
    """
    df = pd.read_sql_query(query, conn)
    return df


@st.cache_data(ttl=600)
def get_statistics():
    """Get basic statistics about the database"""
    conn = get_connection()

    # Total speeches
    total_speeches = pd.read_sql_query(
        "SELECT COUNT(*) as count FROM speeches",
        conn
    ).iloc[0]['count']

    # Total speakers
    total_speakers = pd.read_sql_query(
        "SELECT COUNT(DISTINCT MPID) as count FROM speeches WHERE MPID > 0",
        conn
    ).iloc[0]['count']

    # Speeches by party
    party_counts = pd.read_sql_query(
        """
        SELECT Party, COUNT(*) as count
        FROM speeches
        WHERE Party != '[]' AND Party IS NOT NULL AND Party != ''
        GROUP BY Party
        ORDER BY count DESC
        LIMIT 10
        """,
        conn
    )

    # Speeches over time
    speeches_by_date = pd.read_sql_query(
        """
        SELECT
            strftime('%Y', Date) as Year,
            COUNT(*) as Count
        FROM speeches
        WHERE Date IS NOT NULL
        GROUP BY Year
        ORDER BY Year
        """,
        conn
    )

    return {
        'total_speeches': total_speeches,
        'total_speakers': total_speakers,
        'party_counts': party_counts,
        'speeches_by_date': speeches_by_date
    }


@st.cache_data(ttl=600)
def get_speech_lengths():
    """Get distribution of speech lengths"""
    conn = get_connection()
    query = """
        SELECT
            LENGTH(Speech) as length,
            Party
        FROM speeches
        WHERE Speech IS NOT NULL
        AND Party != '[]' AND Party IS NOT NULL AND Party != ''
        LIMIT 500
    """
    df = pd.read_sql_query(query, conn)
    return df


# Page config
st.set_page_config(
    page_title="SpeakGer Dashboard",
    page_icon=":microphone:",
    layout="wide"
)

# Title
st.title("SpeakGer Parliamentary Speech Dashboard")
st.markdown("Explore German parliamentary speeches from the Bremen dataset")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Choose a view:",
    ["Statistics", "Random Speech", "Visualizations"]
)

# Main content
if page == "Statistics":
    st.header("Database Statistics")

    # Get statistics
    stats = get_statistics()

    # Display metrics
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Speeches", f"{stats['total_speeches']:,}")

    with col2:
        st.metric("Unique Speakers", f"{stats['total_speakers']:,}")

    # Party distribution
    st.subheader("Top 10 Parties by Speech Count")
    if not stats['party_counts'].empty:
        st.dataframe(
            stats['party_counts'],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No party data available")

    # Show SQL query
    with st.expander("View SQL Query"):
        st.code("""
SELECT Party, COUNT(*) as count
FROM speeches
WHERE Party != '[]' AND Party IS NOT NULL AND Party != ''
GROUP BY Party
ORDER BY count DESC
LIMIT 10
        """, language="sql")

elif page == "Random Speech":
    st.header("Random Speech Generator")

    st.markdown("Click the button to get a random speech from the database")

    if st.button("Get Random Speech", type="primary", use_container_width=True):
        speech_df = get_random_speech()

        if not speech_df.empty:
            speech = speech_df.iloc[0]

            # Display metadata
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Speaker", speech['Name'] if pd.notna(speech['Name']) else "Unknown")

            with col2:
                st.metric("Party", speech['Party'] if pd.notna(speech['Party']) and speech['Party'] != '[]' else "Unknown")

            with col3:
                st.metric("Date", speech['Date'] if pd.notna(speech['Date']) else "Unknown")

            # Display speech
            st.subheader("Speech Content")
            st.text_area(
                "Speech",
                speech['Speech'],
                height=300,
                disabled=True,
                label_visibility="collapsed"
            )

            # Show SQL query
            with st.expander("View SQL Query"):
                st.code("""
SELECT
    s.Date,
    s.Party,
    s.Speech,
    m.Name,
    m.SexOrGender
FROM speeches s
LEFT JOIN mps_meta m ON s.MPID = m.MPID
WHERE LENGTH(s.Speech) > 100
ORDER BY RANDOM()
LIMIT 1
                """, language="sql")
        else:
            st.error("No speeches found in the database")

elif page == "Visualizations":
    st.header("Data Visualizations")

    # Get statistics
    stats = get_statistics()

    # Speeches over time
    st.subheader("Speeches Over Time")
    if not stats['speeches_by_date'].empty:
        # Convert Year to numeric
        stats['speeches_by_date']['Year'] = pd.to_numeric(
            stats['speeches_by_date']['Year'],
            errors='coerce'
        )

        fig = px.line(
            stats['speeches_by_date'],
            x='Year',
            y='Count',
            title='Number of Speeches by Year',
            labels={'Count': 'Number of Speeches', 'Year': 'Year'}
        )
        fig.update_traces(line_color='#1f77b4', line_width=3)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No time-series data available")

    # Party distribution bar chart
    st.subheader("Party Distribution")
    if not stats['party_counts'].empty:
        fig = px.bar(
            stats['party_counts'],
            x='Party',
            y='count',
            title='Top 10 Parties by Speech Count',
            labels={'count': 'Number of Speeches', 'Party': 'Party'},
            color='count',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No party data available")

    # Speech length distribution
    st.subheader("Speech Length Distribution")
    with st.spinner("Loading speech length data..."):
        length_df = get_speech_lengths()

        if not length_df.empty:
            fig = px.histogram(
                length_df,
                x='length',
                nbins=50,
                title='Distribution of Speech Lengths (Sample of 500)',
                labels={'length': 'Speech Length (characters)', 'count': 'Frequency'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No speech length data available")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    "This dashboard uses data from the SpeakGer Corpus - "
    "74 years of German parliamentary debates. "
    "Currently showing a sample from Bremen parliament."
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Week 7: Hosting Tutorial")
st.sidebar.caption("Built for MLCI 2025 - Social Data Science")
