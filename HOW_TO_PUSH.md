# How to Push to GitHub

Your SmartGrade Home Assistant integration is ready to push, but authentication is needed.

## ✅ Security Check Complete

**No personal information found in the code:**
- ✅ No actual phone numbers (only examples)
- ✅ No device IDs
- ✅ No JWT tokens
- ✅ No user IDs or domain IDs
- ✅ Safe to push to public repository

## 🚀 Push Options

### Option 1: Personal Access Token (Recommended)

1. **Create a Personal Access Token:**
   - Go to: https://github.com/settings/tokens/new
   - Description: "SmartGrade Home Assistant"
   - Expiration: Choose duration
   - Select scopes: **`repo`** (full control of private repositories)
   - Click "Generate token"
   - **Copy the token** (you won't see it again!)

2. **Push using the token:**
   ```bash
   cd /home/rasp/workspace/homeassistant-smartgrade
   git push https://YOUR_TOKEN_HERE@github.com/itaimain/smartgrade-homeassistant.git main
   ```

3. **Create release tag:**
   ```bash
   git tag -a v1.0.0 -m "Initial release v1.0.0"
   git push https://YOUR_TOKEN_HERE@github.com/itaimain/smartgrade-homeassistant.git v1.0.0
   ```

### Option 2: SSH Key

1. **Check if you already have an SSH key:**
   ```bash
   ls -la ~/.ssh/id_*.pub
   ```

2. **If not, generate one:**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Press Enter for default location
   # Enter a passphrase (optional but recommended)
   ```

3. **Copy the public key:**
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

4. **Add to GitHub:**
   - Go to: https://github.com/settings/keys
   - Click "New SSH key"
   - Title: "Raspberry Pi"
   - Paste the public key
   - Click "Add SSH key"

5. **Test SSH connection:**
   ```bash
   ssh -T git@github.com
   # Should see: "Hi itaimain! You've successfully authenticated..."
   ```

6. **Push to GitHub:**
   ```bash
   cd /home/rasp/workspace/homeassistant-smartgrade
   git remote set-url origin git@github.com:itaimain/smartgrade-homeassistant.git
   git push -u origin main
   git tag -a v1.0.0 -m "Initial release v1.0.0"
   git push origin v1.0.0
   ```

### Option 3: Use the Script

Run the provided script:
```bash
cd /home/rasp/workspace/homeassistant-smartgrade
./PUSH_TO_GITHUB.sh
```

It will:
- Check SSH authentication
- Push if SSH works
- Show detailed instructions if not

### Option 4: Push from Another Machine

1. **Copy the repository:**
   ```bash
   # On your local machine
   scp -r rasp@your-pi-ip:/home/rasp/workspace/homeassistant-smartgrade ~/
   cd ~/homeassistant-smartgrade
   ```

2. **Push:**
   ```bash
   git remote set-url origin git@github.com:itaimain/smartgrade-homeassistant.git
   git push -u origin main
   git tag -a v1.0.0 -m "Initial release v1.0.0"
   git push origin v1.0.0
   ```

## 📋 After Pushing

Once the code is on GitHub:

1. **Create a Release:**
   - Go to: https://github.com/itaimain/smartgrade-homeassistant/releases
   - Click "Create a new release"
   - Choose tag: `v1.0.0`
   - Title: `v1.0.0 - Initial Release`
   - Description: Copy from CHANGELOG.md
   - Publish release

2. **Test Installation:**
   - In Home Assistant, go to HACS
   - Click ⋮ (three dots) → Custom repositories
   - Repository: `https://github.com/itaimain/smartgrade-homeassistant`
   - Category: Integration
   - Click Add
   - Search for "SmartGrade"
   - Install

3. **Announce:**
   - Home Assistant Community Forum
   - Reddit r/homeassistant
   - Share with SmartGrade users

## 🔐 Security Note

The repository has been checked and contains NO personal information:
- Phone numbers are only examples (0501234567)
- No actual tokens or credentials
- No device IDs
- Safe for public repository

## ❓ Troubleshooting

**"Permission denied"**
- Your SSH key doesn't have write access
- Use Personal Access Token instead (Option 1)

**"could not read Username"**
- HTTPS requires credentials
- Use Personal Access Token or SSH key

**"Repository not found"**
- Make sure the repository exists on GitHub
- Check the URL is correct: https://github.com/itaimain/smartgrade-homeassistant

## 📞 Need Help?

If you're stuck, you can also:
1. Manually copy the files to GitHub via the web interface
2. Use GitHub Desktop application
3. Ask for help in GitHub Discussions

---

**Repository Path:** `/home/rasp/workspace/homeassistant-smartgrade`  
**Remote URL:** `https://github.com/itaimain/smartgrade-homeassistant.git`  
**Current Commit:** Initial release v1.0.0 (26 files, 3845 lines)
