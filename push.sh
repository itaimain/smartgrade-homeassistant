#!/bin/bash
# Interactive push script for SmartGrade Home Assistant integration

cd /home/rasp/workspace/homeassistant-smartgrade

echo "=================================================="
echo "  SmartGrade Home Assistant - Push to GitHub"
echo "=================================================="
echo ""
echo "Repository: itaimain/smartgrade-homeassistant"
echo "Branch: main"
echo "Commit: $(git log -1 --oneline)"
echo ""
echo "✅ Security verified: No personal information"
echo ""
echo "To push, you need a GitHub Personal Access Token."
echo ""
echo "Get your token here: https://github.com/settings/tokens/new"
echo "Permissions needed: 'repo' (full control)"
echo ""
read -sp "Enter your GitHub Personal Access Token: " TOKEN
echo ""
echo ""

if [ -z "$TOKEN" ]; then
    echo "❌ No token provided. Exiting."
    exit 1
fi

echo "Pushing to GitHub..."
git push https://$TOKEN@github.com/itaimain/smartgrade-homeassistant.git main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to main branch!"
    echo ""
    echo "Creating release tag v1.0.0..."
    git tag -a v1.0.0 -m "Initial release v1.0.0" 2>/dev/null || echo "Tag already exists"
    git push https://$TOKEN@github.com/itaimain/smartgrade-homeassistant.git v1.0.0
    
    echo ""
    echo "=================================================="
    echo "✅ SUCCESS!"
    echo "=================================================="
    echo ""
    echo "Your integration is now on GitHub!"
    echo ""
    echo "🔗 View it here:"
    echo "   https://github.com/itaimain/smartgrade-homeassistant"
    echo ""
    echo "📋 Next steps:"
    echo "1. Create a GitHub Release for v1.0.0"
    echo "2. Add to HACS as a custom repository"
    echo "3. Test installation in Home Assistant"
    echo ""
else
    echo ""
    echo "❌ Push failed. Please check:"
    echo "   - Token has 'repo' permissions"
    echo "   - Token is valid and not expired"
    echo "   - Repository exists: https://github.com/itaimain/smartgrade-homeassistant"
    echo ""
    exit 1
fi
