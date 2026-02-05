# Quick Start Guide - Push to GitHub

## 🚀 5-Minute Setup

### Step 1: Create GitHub Repository (2 minutes)

1. Go to https://github.com/new
2. Repository name: **`homeassistant-smartgrade`**
3. Description: **`SmartGrade integration for Home Assistant`**
4. **Public** repository
5. **Do NOT** check "Initialize this repository with a README"
6. Click **"Create repository"**

### Step 2: Update Your Username (1 minute)

Replace `itaimain` with your actual GitHub username:

```bash
cd /home/rasp/workspace/homeassistant-smartgrade

# Replace in all files (Linux/Mac)
find . -type f \( -name "*.md" -o -name "*.json" \) -not -path "./.git/*" | \
  xargs sed -i 's/itaimain/your_actual_username/g'

# Or manually edit:
# - README.md (2 locations)
# - info.md (1 location)
# - custom_components/smartgrade/manifest.json (2 locations)
```

### Step 3: Push to GitHub (2 minutes)

```bash
cd /home/rasp/workspace/homeassistant-smartgrade

# Stage all files
git add .

# Initial commit
git commit -m "Initial release v1.0.0"

# Add remote (replace itaimain with your GitHub username)
git remote add origin https://github.com/itaimain/homeassistant-smartgrade.git

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main

# Create release tag
git tag -a v1.0.0 -m "Initial release v1.0.0"
git push origin v1.0.0
```

### Step 4: Create GitHub Release

1. Go to your repository: `https://github.com/itaimain/homeassistant-smartgrade`
2. Click **"Releases"** → **"Create a new release"**
3. **Choose a tag**: Select `v1.0.0`
4. **Release title**: `v1.0.0 - Initial Release`
5. **Description**: Copy from CHANGELOG.md
6. Click **"Publish release"**

## ✅ Done! Your integration is now on GitHub

### Install via HACS (Custom Repository)

Users can now install your integration:

1. Open HACS in Home Assistant
2. Click **⋮** (three dots) → **Custom repositories**
3. **Repository**: `https://github.com/itaimain/homeassistant-smartgrade`
4. **Category**: Integration
5. Click **"Add"**
6. Search for "SmartGrade"
7. Click **"Download"**
8. Restart Home Assistant

### Submit to HACS Default (Optional)

To make it appear in HACS search by default:

1. Fork https://github.com/hacs/default
2. Edit the `integration` file
3. Add line: `itaimain/homeassistant-smartgrade`
4. Create Pull Request
5. Wait for approval (1-3 days)

## 📋 Verification Checklist

After pushing, verify on GitHub:

- [ ] All files are visible
- [ ] README.md displays correctly
- [ ] Release v1.0.0 exists
- [ ] GitHub Actions passed (check Actions tab)
- [ ] No errors in workflows

## 🎯 Share Your Integration

Announce on:

- **Home Assistant Community**: https://community.home-assistant.io/
- **Reddit**: r/homeassistant
- **Discord**: Home Assistant server (#custom-integrations)

Example announcement:
```
🎉 New Integration: SmartGrade for Home Assistant

Control SmartGrade devices (switches, water heaters) directly from Home Assistant!

Features:
✅ Phone + SMS authentication
✅ Real-time MQTT updates
✅ Timer management
✅ Energy monitoring

Install via HACS: https://github.com/itaimain/homeassistant-smartgrade

Feedback welcome!
```

## 🆘 Troubleshooting

**Problem**: "remote: Repository not found"
- **Solution**: Check repository name matches exactly
- **Solution**: Verify you have write access to the repository

**Problem**: "Updates were rejected"
- **Solution**: Run `git pull origin main` first, then push again

**Problem**: GitHub Actions failing
- **Solution**: Check `.github/workflows/validate.yaml` for errors
- **Solution**: Ensure hacs.json and manifest.json are valid JSON

**Problem**: HACS not finding integration
- **Solution**: Ensure you created a release (v1.0.0 tag)
- **Solution**: Check hacs.json file exists at repository root
- **Solution**: Wait a few minutes for GitHub to update

## 📞 Support

Need help?
- **HACS Discord**: https://discord.gg/apgchf8
- **Home Assistant Discord**: https://discord.gg/home-assistant
- **Community Forum**: https://community.home-assistant.io/

---

**Next**: See `SETUP_GUIDE.md` for detailed instructions and maintenance tips.
