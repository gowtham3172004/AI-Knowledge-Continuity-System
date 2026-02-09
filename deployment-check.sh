#!/bin/bash

# Deployment Pre-flight Checker
# Run this script before deploying to catch common issues

echo "🔍 AI Knowledge Continuity System - Deployment Checker"
echo "=================================================="
echo ""

# Check 1: Git repository
echo "✓ Checking Git repository..."
if [ -d .git ]; then
    echo "  ✅ Git initialized"
else
    echo "  ❌ Git not initialized. Run: git init"
    exit 1
fi

# Check 2: Environment files
echo ""
echo "✓ Checking environment files..."
if [ -f ".env" ]; then
    echo "  ✅ .env file exists"
    
    # Check for Gemini API key
    if grep -q "GEMINI_API_KEY=" .env; then
        if grep -q "your_gemini_api_key_here" .env; then
            echo "  ⚠️  WARNING: GEMINI_API_KEY not set (still placeholder)"
        else
            echo "  ✅ GEMINI_API_KEY is set"
        fi
    else
        echo "  ❌ GEMINI_API_KEY not found in .env"
    fi
else
    echo "  ⚠️  .env file not found (okay if using Railway env vars)"
fi

# Check 3: Dependencies
echo ""
echo "✓ Checking dependencies..."
if [ -f "requirements.txt" ]; then
    echo "  ✅ requirements.txt exists"
else
    echo "  ❌ requirements.txt missing"
    exit 1
fi

if [ -f "frontend/package.json" ]; then
    echo "  ✅ frontend/package.json exists"
else
    echo "  ❌ frontend/package.json missing"
    exit 1
fi

# Check 4: Build files
echo ""
echo "✓ Checking configuration files..."
if [ -f "vercel.json" ]; then
    echo "  ✅ vercel.json exists"
else
    echo "  ⚠️  vercel.json not found"
fi

if [ -f "railway.json" ]; then
    echo "  ✅ railway.json exists"
else
    echo "  ⚠️  railway.json not found"
fi

# Check 5: Required directories
echo ""
echo "✓ Checking project structure..."
required_dirs=("backend" "frontend" "data" "rag" "vector_store")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir/ exists"
    else
        echo "  ❌ $dir/ missing"
    fi
done

# Check 6: Python version
echo ""
echo "✓ Checking Python version..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    echo "  ✅ Python $python_version installed"
    
    # Check if version is 3.10+
    major=$(echo $python_version | cut -d. -f1)
    minor=$(echo $python_version | cut -d. -f2)
    if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
        echo "  ✅ Python version is 3.10+"
    else
        echo "  ⚠️  WARNING: Python 3.10+ recommended (you have $python_version)"
    fi
else
    echo "  ❌ Python not found"
fi

# Check 7: Node version
echo ""
echo "✓ Checking Node.js version..."
if command -v node &> /dev/null; then
    node_version=$(node --version)
    echo "  ✅ Node.js $node_version installed"
else
    echo "  ❌ Node.js not found"
fi

# Check 8: Git status
echo ""
echo "✓ Checking Git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo "  ⚠️  WARNING: You have uncommitted changes"
    echo "     Run: git add . && git commit -m 'Ready for deployment'"
else
    echo "  ✅ All changes committed"
fi

# Check 9: GitHub remote
echo ""
echo "✓ Checking GitHub remote..."
if git remote get-url origin &> /dev/null; then
    remote_url=$(git remote get-url origin)
    echo "  ✅ GitHub remote configured: $remote_url"
else
    echo "  ⚠️  No GitHub remote found"
    echo "     Add one with: git remote add origin <your-repo-url>"
fi

# Summary
echo ""
echo "=================================================="
echo "🎯 Pre-flight Check Complete!"
echo ""
echo "📋 Next Steps:"
echo "   1. Fix any ❌ errors above"
echo "   2. Review ⚠️  warnings"
echo "   3. Push to GitHub: git push origin main"
echo "   4. Deploy backend to Railway"
echo "   5. Deploy frontend to Vercel"
echo ""
echo "📖 Full guide: FREE_DEPLOYMENT_GUIDE.md"
echo "=================================================="
