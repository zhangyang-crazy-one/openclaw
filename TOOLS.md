# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Node.js Environment

### Node Version Manager (nvm)
```bash
# 加载nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 使用特定版本
nvm use 22

# 安装新版本
nvm install 22
```

### pnpm (Node Package Manager)
```bash
# 全局安装
pnpm add -g <package>

# 运行脚本
pnpm exec <command>

# 使用本地node_modules
pnpm run <script>
```

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without losing your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
