# 🚀 Git 推送操作指南

## 当前状态
✅ 远程仓库已配置：https://github.com/Wzh2learn/agents_final_tech.git
✅ Git 凭据存储已设置
⏳ 等待身份验证

---

## 方案一：使用 Personal Access Token（推荐新手）

### 步骤 1：创建 GitHub Personal Access Token

1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 配置 Token：
   - **Note**: 输入 `accounting-rules-assistant`
   - **Expiration**: 选择 `No expiration` 或 90 天
   - **Select scopes**: 勾选 `repo`（完整的仓库访问权限）
4. 点击 "Generate token"
5. **重要**：复制生成的 token（只显示一次！）

### 步骤 2：推送代码

```bash
# 在项目目录下执行
cd /workspace/projects

# 推送代码（会提示输入用户名和密码）
git push -u origin main
```

当提示时：
- **Username**: `Wzh2learn`
- **Password**: 粘贴刚才复制的 Personal Access Token

### 步骤 3：验证推送成功

1. 访问：https://github.com/Wzh2learn/agents_final_tech
2. 查看代码是否已成功推送

---

## 方案二：使用 SSH 密钥（推荐）

### 步骤 1：生成 SSH 密钥

```bash
# 生成新的 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 一路回车（使用默认路径和空密码）
```

### 步骤 2：查看公钥

```bash
# 查看公钥内容
cat ~/.ssh/id_ed25519.pub
```

### 步骤 3：添加 SSH 密钥到 GitHub

1. 访问：https://github.com/settings/keys
2. 点击 "New SSH key"
3. 填写：
   - **Title**: `My Computer`
   - **Key**: 粘贴刚才查看的公钥内容（从 `ssh-ed25519` 开始到邮箱结束）
4. 点击 "Add SSH key"

### 步骤 4：切换远程仓库为 SSH

```bash
# 修改远程仓库 URL 为 SSH
cd /workspace/projects
git remote set-url origin git@github.com:Wzh2learn/agents_final_tech.git

# 验证修改
git remote -v
```

### 步骤 5：推送代码

```bash
# 推送代码（无需输入密码）
git push -u origin main
```

### 步骤 6：验证推送成功

1. 访问：https://github.com/Wzh2learn/agents_final_tech
2. 查看代码是否已成功推送

---

## 方案三：使用 GitHub CLI（最简单）

### 步骤 1：安装 GitHub CLI

```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# Windows
# 下载安装：https://github.com/cli/cli/releases
```

### 步骤 2：登录 GitHub

```bash
# 登录
gh auth login

# 按提示选择：
# - What account do you want to log into? → GitHub.com
# - What is your preferred protocol for Git operations? → HTTPS
# - Authenticate Git with your GitHub credential? → Yes
# - How would you like to authenticate GitHub CLI? → Login with a web browser
```

### 步骤 3：推送代码

```bash
# 推送代码
git push -u origin main
```

---

## 💡 推荐操作步骤

**最快方式（使用 Personal Access Token）**：

1. 访问 https://github.com/settings/tokens 生成 token
2. 执行：
   ```bash
   cd /workspace/projects
   git push -u origin main
   ```
3. 输入用户名：`Wzh2learn`
4. 输入密码：粘贴 token

---

## ❗ 常见问题

### Q: 提示 "Authentication Failed"
**A**: 确保使用正确的 token 或检查 SSH 密钥是否正确添加

### Q: 提示 "Repository not found"
**A**: 确保仓库 URL 正确，且你有访问权限

### Q: 推送速度很慢
**A**: 检查网络连接，或使用 SSH 方式（通常更快）

### Q: 如何撤销已推送的提交
**A**:
```bash
# 撤销最后一次提交（保留修改）
git reset --soft HEAD~1
git push origin main --force

# 撤销最后一次提交（删除修改）
git reset --hard HEAD~1
git push origin main --force
```

---

## 🎉 推送成功后

你的项目已经发布到：
https://github.com/Wzh2learn/agents_final_tech

### 下一步可以做的事：
1. ✅ 在本地克隆项目：`git clone https://github.com/Wzh2learn/agents_final_tech.git`
2. ✅ 配置 GitHub Pages（创建文档网站）
3. ✅ 设置 GitHub Actions（自动化测试和部署）
4. ✅ 添加协作者（Settings → Collaborators）
5. ✅ 创建 Issues 和 Wiki

---

**祝你使用愉快！🎊**
