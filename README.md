# 防火墙VPN技术与应用实验仓库

## 目录结构

```
repo/
├── homework/                # 老师发布的作业题目
│   ├── Lab1/
│   │   ├── Lab1.md (文件名仅为参考)
│   └── Lab2/
├── 学号姓名/                 # 每位同学自己的文件夹
│   ├── Lab1/
│   │   │── 作业文件.py (文件名仅为参考，具体要看作业文件)
│   │   │── 说明文件.md (文件名仅为参考，具体要看作业文件)
│   └── Lab2/
└── README.md
```

---

## 第一次配置（只需做一次）

fork 并 clone 仓库后，需要绑定老师的仓库地址，用于后续同步新作业：

```bash
git remote add upstream https://github.com/LiuXiYing/FirewallVPNTechnologyAndApplications.git
```

验证是否成功：

```bash
git remote -v
```

看到以下输出即表示配置成功：

```
origin    https://github.com/你的账号/仓库名.git (fetch)
origin    https://github.com/你的账号/仓库名.git (push)
upstream  https://github.com/LiuXiYing/FirewallVPNTechnologyAndApplications.git (fetch)
upstream  https://github.com/LiuXiYing/FirewallVPNTechnologyAndApplications.git (push)
```

---

## 每次作业流程

### 1. 同步新题目

```bash
git pull upstream main
```

### 2. 在自己的文件夹下新建本次作业目录，完成作业(以第一次作业为例)

```
学号姓名/
└── Lab1/          (注意大小写)
    └── Lab1.md
```

### 3. 提交并推送

```bash
git add .
git commit -m "描述此次提交的改动"
git push 
```

### 4. 发起 PR

前往自己 fork 的仓库页面，点击 `Contribute → Open pull request`，向老师的 `main` 分支发起 PR。

---

## PR 填写规范

**标题：**

```
[学号姓名]Lab1作业提交
```

例如：`[2024010002王诗惠]Lab1作业提交`

**描述：**

```
## 说明
（选填，写写思路或遇到的问题）
```

---

## 注意事项

- 只能修改**自己的文件夹**，不要动其他同学的目录
- PR 提交后如发现有问题，直接在本地修改后 `push`，PR 会自动更新，**不需要重新发**
- 截止时间后提交的 PR 不予受理
- 涉及截图的作业，严禁使用**拍屏幕**的方式来代替截图提交
