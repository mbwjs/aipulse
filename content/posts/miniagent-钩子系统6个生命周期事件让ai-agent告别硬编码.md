---
slug: "miniagent-钩子系统6个生命周期事件让ai-agent告别硬编码"
date: '2026-06-23T04:14:39+08:00'
draft: false
title: 'MiniAgent 钩子系统：6个生命周期事件让AI Agent告别硬编码'
---

## 背景

MiniAgent 是一个 450 行 Python 单文件的 VPS AI Agent。之前的自动化全是硬编码——在函数里顺手调个 `git commit`、启动时检查下 SSH remote——不通用、不可配、不可扩展。

这周受 Anthropic 7月发布的 [Claude Code Hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) 启发，给 MiniAgent 也加了一套轻量钩子系统。

## 核心设计

### 一条 JSON 配置，六种生命周期事件

```json
{
  "hooks": {
    "SessionStart": [],
    "SessionEnd": [],
    "UserPromptSubmit": [],
    "PreToolUse": [
      {"matcher": "bash", "command": "block-dangerous-ops.sh"}
    ],
    "PostToolUse": [
      {"matcher": "write|edit", "command": "git add -A && git commit -m 'auto-backup'"}
    ],
    "PostToolUseFailure": []
  }
}
```

### Handler 契约极简

- **stdin** 接收 JSON 上下文：`{"event":"PreToolUse","tool_name":"bash","tool_input":{...}}`
- **exit 0** → 放行，stdout 作为通知显示
- **exit 2** → 阻断，stdout 作为阻断原因
- **超时 10s** → 不阻断，记录日志
- Handler 目前只支持 shell 命令（HTTP / LLM 子提示词后续加）

### 事件说明

| 事件 | 触发点 | 可阻断 |
|------|--------|--------|
| `SessionStart` | 会话启动时 | ❌ |
| `SessionEnd` | 键入 `q` 退出 | ❌ |
| `UserPromptSubmit` | 用户按下回车后 | ✅ |
| `PreToolUse` | 工具执行之前 | ✅ |
| `PostToolUse` | 工具成功执行后 | ❌ |
| `PostToolUseFailure` | 工具执行失败后 | ❌ |

## 实际用例

### 1. PostToolUse → 每次写文件自动 git commit

```json
{
  "matcher": "write|edit",
  "command": "cd /root/miniagent && git add -A && git diff --cached --quiet || git commit -m 'Hook: auto-commit'"
}
```

配合默认规则"写代码后提交"，现在彻底自动化，不需要每次手动 `/stable`。

### 2. PreToolUse → 拦截危险命令

```json
{
  "matcher": "bash",
  "command": "jq -r '.tool_input.command' | grep -qE 'rm -rf|shutdown' && exit 2 || exit 0"
}
```

MiniAgent 本身有字符串黑名单（`rm -rf /` 等），但钩子让规则可外部配置，不需要改源码。

### 3. UserPromptSubmit → 注入上下文或合规审查

可以接入敏感词过滤、自动注入当前时间戳、检查是否包含泄露的 API key。

## 与 Claude Code Hooks 的对比

| | Claude Code Hooks | MiniAgent Hooks |
|---|---|---|
| 事件数 | 30+ | 6 |
| Handler 类型 | Shell / HTTP / LLM 子提示词 | Shell only（暂时） |
| 异步钩子 | ✅ | ❌ |
| 配置方式 | `.claude/settings.json` | `hooks.json` |
| 复杂度 | 高（权限控制、channel、插件） | 极简（一个 dict + 一个 dispatch 函数） |
| 代码量 | 内核级 | ~60 行 Python |

MiniAgent 的钩子系统追求的是 **80% 场景用 20% 复杂度**。六个事件覆盖了最需要自动化的节点，一个 JSON 文件就搞定。

## 部署

所有代码已推送到 [github.com/mbwjs/miniagent](https://github.com/mbwjs/miniagent)，`hooks.json` 和 AGENT.md 里都有文档。`/hooks` 命令可以查看当前注册的全部钩子。

下一步计划加 HTTP handler 支持（这样就能在 PostToolUse 后回调外部 CI/CD），以及异步钩子（不阻塞 LLM 响应）。
