#!/bin/bash

# Run Streamlit dashboard with uv

echo ""
echo "=========================================="
echo "Starting SpeakGer Dashboard"
echo "=========================================="
echo ""
echo "Server will start on: http://localhost:8501"
echo "Press CTRL+C to stop"
echo ""

uvx --with streamlit --with pandas --with plotly streamlit run dashboard.py
