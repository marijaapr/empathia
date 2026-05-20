#!/bin/bash
# EMPATHIA PSYCHOLOGIST SYSTEM - QUICK SETUP

echo "=========================================="
echo "Empathia Psychologist Integration Setup"
echo "=========================================="
echo ""

# Step 1: Check if files exist
echo "✓ Checking files..."
files=(
    "services/psychologist/service.py"
    "services/psychologist/realtime.py"
    "services/emotion_analyzer.py"
    "routes/psychologist_routes.py"
    "database/psychologist_migration.sql"
    "templates/psychologist/dashboard.html"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (MISSING)"
    fi
done

echo ""
echo "=========================================="
echo "NEXT STEPS:"
echo "=========================================="
echo ""
echo "1. GO TO SUPABASE CONSOLE"
echo "   - Click 'SQL Editor'"
echo "   - Click 'New Query'"
echo ""
echo "2. COPY & PASTE SQL"
echo "   - Open: database/psychologist_migration.sql"
echo "   - Copy all content"
echo "   - Paste into Supabase SQL Editor"
echo "   - Click 'Run'"
echo ""
echo "3. WAIT FOR SUCCESS"
echo "   - You should see 'Query executed successfully'"
echo ""
echo "4. UPDATE .env"
echo "   Make sure you have:"
echo "   - SUPABASE_URL=your_url"
echo "   - SUPABASE_KEY=your_key"
echo ""
echo "5. UPDATE requirements.txt"
echo "   Add these lines:"
echo "   - supabase==2.0.0"
echo "   - asyncio==3.4.3"
echo ""
echo "6. INSTALL DEPENDENCIES"
echo "   pip install -r requirements.txt"
echo ""
echo "7. UPDATE app.py"
echo "   Add:"
echo "   from routes.psychologist_routes import psychologist_bp"
echo "   from services.emotion_analyzer import EmotionDetector"
echo "   app.register_blueprint(psychologist_bp)"
echo ""
echo "8. TEST ENDPOINTS"
echo "   curl http://localhost:5001/api/psychologist/health"
echo ""
echo "=========================================="
echo "All set! Follow the steps above."
echo "=========================================="
