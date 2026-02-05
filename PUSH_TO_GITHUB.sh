#!/bin/bash
# Script to push SmartGrade Home Assistant integration to GitHub

echo "=========================================="
echo "SmartGrade Home Assistant - Push to GitHub"
echo "=========================================="
echo ""

cd /home/rasp/workspace/homeassistant-smartgrade

echo "Repository: https://github.com/itaimain/smartgrade-homeassistant.git"
echo "Current branch: $(git branch --show-current)"
echo "Commit: $(git log -1 --oneline)"
echo ""
echo "Status:"
git status --short
echo ""

# Check if we have SSH access
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "✓ SSH authentication works"
    echo "Pushing with SSH..."
    git remote set-url origin git@github.com:itaimain/smartgrade-homeassistant.git
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ Successfully pushed to GitHub!"
        echo ""
        echo "Creating release tag v1.0.0..."
        git tag -a v1.0.0 -m "Initial release v1.0.0"
        git push origin v1.0.0
        
        echo ""
        echo "=========================================="
        echo "✓ SUCCESS!"
        echo "=========================================="
        echo ""
        echo "Next steps:"
        echo "1. Visit: https://github.com/itaimain/smartgrade-homeassistant"
        echo "2. Create a release for v1.0.0"
        echo "3. Add to HACS as custom repository"
        echo ""
    else
        echo "✗ Push failed with SSH"
        exit 1
    fi
else
    echo "✗ SSH authentication not configured"
    echo ""
    echo "Please use one of these methods to push:"
    echo ""
    echo "Option 1: Use Personal Access Token (Recommended)"
    echo "==========================================="
    echo "1. Create token: https://github.com/settings/tokens/new"
    echo "   - Select: repo (full control)"
    echo "2. Run:"
    echo "   cd /home/rasp/workspace/homeassistant-smartgrade"
    echo "   git push https://YOUR_TOKEN@github.com/itaimain/smartgrade-homeassistant.git main"
    echo ""
    echo "Option 2: Configure SSH Key"
    echo "========================="
    echo "1. Generate key: ssh-keygen -t ed25519 -C 'your_email@example.com'"
    echo "2. Add to GitHub: https://github.com/settings/keys"
    echo "3. Run this script again"
    echo ""
    echo "Option 3: Push from Local Machine"
    echo "=================================="
    echo "1. Copy repository to your local machine"
    echo "2. Run: git remote set-url origin git@github.com:itaimain/smartgrade-homeassistant.git"
    echo "3. Run: git push -u origin main"
    echo ""
fi
