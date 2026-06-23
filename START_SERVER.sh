#!/bin/bash

# Start API Server and Streamlit UI for Loan Agent System

PROJECT_DIR="/home/ubuntu/Desktop/Loan_Agent_Project"
VENV_DIR="$PROJECT_DIR/.venv"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Set API key
export ANTHROPIC_API_KEY='sk-MbT3EUpbEfx06ORb3FnfjA'

# Change to project directory
cd "$PROJECT_DIR/loan_ai_system"

echo "================================================"
echo "   Loan Agent System - Starting Services"
echo "================================================"
echo ""
echo "✅ Virtual environment activated"
echo "✅ API key configured"
echo ""

# Start API server in the background
echo "🚀 Starting API Server on port 8000..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
echo "   API Server PID: $API_PID"
sleep 3

# Check if API is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API Server is running!"
else
    echo "⚠️  API Server may be starting..."
fi

echo ""
echo "================================================"
echo "   Opening Streamlit UI in 5 seconds..."
echo "================================================"
echo ""

sleep 5

# Start Streamlit UI
echo "🚀 Starting Streamlit UI on port 8501..."
echo ""
streamlit run ui/app.py --server.port=8501 --logger.level=info

# Cleanup on exit
trap "kill $API_PID" EXIT
