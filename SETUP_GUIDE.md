# GitHub Repository Setup Guide

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `homeassistant-smartgrade`
3. Description: `SmartGrade integration for Home Assistant`
4. Public repository
5. **Do NOT** initialize with README (we have our own)
6. Click "Create repository"

## Step 2: Push Code to GitHub

```bash
cd /home/rasp/workspace/homeassistant-smartgrade

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial release v1.0.0"

# Add remote (replace itaimain with your GitHub username)
git remote add origin https://github.com/itaimain/homeassistant-smartgrade.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Create Release

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Tag version: `v1.0.0`
4. Release title: `v1.0.0 - Initial Release`
5. Description: Copy from CHANGELOG.md
6. Click "Publish release"

## Step 4: Update URLs in Files

Replace `itaimain` with your actual GitHub username in:

- `README.md` (multiple locations)
- `info.md` (links section)
- `custom_components/smartgrade/manifest.json` (documentation and issue_tracker)
- `CHANGELOG.md` (release links)

Use find and replace:
```bash
cd /home/rasp/workspace/homeassistant-smartgrade
find . -type f -name "*.md" -o -name "*.json" | xargs sed -i 's/itaimain/actual_username/g'
```

## Step 5: Add to HACS

### Option A: HACS Default (Recommended)

1. Go to https://github.com/hacs/default
2. Fork the repository
3. Edit `integration` file
4. Add your repository at the end:
   ```
   itaimain/homeassistant-smartgrade
   ```
5. Commit and create Pull Request
6. Wait for approval (usually takes a few days)

### Option B: HACS Custom Repository (Immediate)

Users can add your integration immediately as a custom repository:

1. In Home Assistant, go to HACS
2. Click the three dots in the top right
3. Select "Custom repositories"
4. Add repository URL: `https://github.com/itaimain/homeassistant-smartgrade`
5. Category: "Integration"
6. Click "Add"

## Step 6: Test Installation

1. In Home Assistant with HACS installed
2. Go to HACS → Integrations
3. Click "+" button
4. Search for "SmartGrade"
5. Click Install
6. Restart Home Assistant
7. Add integration via Settings → Devices & Services

## Step 7: Repository Settings

### Enable Issues
- Settings → General → Features → Issues (checked)

### Enable Discussions (Optional)
- Settings → General → Features → Discussions (checked)

### Add Topics
- Settings → General → Topics
- Add: `home-assistant`, `hacs`, `smart-home`, `smartgrade`, `home-automation`

### Add Description
- Settings → General → Description
- `SmartGrade integration for Home Assistant`
- Website: `https://www.smartgrade.co.il/`

### Branch Protection (Optional)
- Settings → Branches → Add rule
- Branch name pattern: `main`
- Require pull request reviews before merging
- Require status checks to pass before merging

## Step 8: Documentation

### Update README.md
Replace the placeholder badge URL in README.md:
```markdown
[![GitHub Release](https://img.shields.io/github/release/itaimain/homeassistant-smartgrade.svg?style=for-the-badge)](https://github.com/itaimain/homeassistant-smartgrade/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/m/itaimain/homeassistant-smartgrade.svg?style=for-the-badge)](https://github.com/itaimain/homeassistant-smartgrade/commits/main)
[![License](https://img.shields.io/github/license/itaimain/homeassistant-smartgrade.svg?style=for-the-badge)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
```

Add these at the top of README.md.

## Step 9: Announce

Share your integration:

1. **Home Assistant Community Forum**
   - https://community.home-assistant.io/
   - Category: "Share Your Projects"
   - Title: "SmartGrade Integration - Control SmartGrade devices in Home Assistant"

2. **Reddit**
   - r/homeassistant
   - Post: "I created a Home Assistant integration for SmartGrade devices"

3. **Home Assistant Discord**
   - #custom-integrations channel

## Maintenance

### Version Updates

When releasing new versions:

1. Update version in `custom_components/smartgrade/manifest.json`
2. Update `CHANGELOG.md` with changes
3. Commit changes
4. Create new release on GitHub with version tag (e.g., `v1.1.0`)

### Responding to Issues

- Be responsive to bug reports
- Ask for logs when needed
- Close issues when resolved
- Thank contributors

## HACS Submission Checklist

Before submitting to HACS default:

- [ ] Repository is public
- [ ] Has releases (at least v1.0.0)
- [ ] Has README.md with installation instructions
- [ ] Has hacs.json file
- [ ] Has info.md file
- [ ] Passes HACS validation (GitHub Actions)
- [ ] Passes Hassfest validation
- [ ] Integration works in Home Assistant
- [ ] No hardcoded credentials in code
- [ ] Proper error handling
- [ ] Follows Home Assistant coding standards

## Support

If you need help:
- HACS Discord: https://discord.gg/apgchf8
- Home Assistant Community: https://community.home-assistant.io/
- Home Assistant Discord: https://discord.gg/home-assistant

## Quick Commands Reference

```bash
# Create release
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0

# Update to new version
# 1. Edit manifest.json version
# 2. Update CHANGELOG.md
git add .
git commit -m "Release v1.1.0"
git tag -a v1.1.0 -m "Version 1.1.0"
git push origin main
git push origin v1.1.0
```
