import os
import streamlit as st
import pyodbc
import pandas as pd
import altair as alt


# Custom CSS for purple button
st.markdown("""
    <style>
    button[kind="primary"] { background: #8b5cf6; border-color: #8b5cf6; }
    button[kind="primary"]:hover { background: #7c3aed; border-color: #7c3aed; }
    </style>
""", unsafe_allow_html=True)


# Streamlit UI
st.title("BTC Price Tracker", text_alignment="center")


# SQL Server connection configuration from environment variables
instance_name = os.getenv('SQL_SERVER_HOST', 'sqlServer')
database_name = os.getenv('SQL_DATABASE', 'Cryptocurrency')
username = os.getenv('SQL_USERNAME', 'sa')
password = os.getenv('SA_PASSWORD') or os.getenv('SQL_PASSWORD')
port = os.getenv('SQL_PORT', '1433')


if not password:
    st.error("SA_PASSWORD (or SQL_PASSWORD) environment variable is required")
    st.stop()


def fetch_data():
    conn = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={instance_name},{port};'
        f'DATABASE={database_name};'
        f'UID={username};'
        f'PWD={password};'
    )
    query = '''SELECT DATETIME, Price FROM Bitcoin ORDER BY DATETIME ASC'''
    df = pd.read_sql(query, conn)
    conn.close()
    return df


if st.button("Fetch Bitcoin Prices", type="primary"):
    try:
        df = fetch_data()
        
        if not df.empty:
            st.success(f"Fetched {len(df)} records")
            
            # Format datetime for display (remove microseconds)
            df['DATETIME'] = df['DATETIME'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            latest = df.iloc[-1]
            st.metric("Latest Bitcoin Price", f"${latest['Price']:,.2f}", 
                     f"At {latest['DATETIME']}")
            
            st.subheader("Price Over Time")
            
            # Use Altair for better y-axis scaling
            chart = alt.Chart(df).mark_line(point=True).encode(
                x=alt.X('DATETIME:T', title='Time'),
                y=alt.Y('Price:Q', title='Price (USD)', scale=alt.Scale(zero=False)),
                tooltip=['DATETIME:T', 'Price:Q']
            ).properties(
                width='container',
                height=400
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
            
            with st.expander("Show Raw Data"):
                st.dataframe(df)
        else:
            st.error("No data found.")

    except Exception as e:
        st.error(f"Error: {e}")
