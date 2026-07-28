# styles/_disabled/ — 暂禁用的风格包

此目录下的包**未完成、暂不 offer 给生产**。`_` 前缀 = 非在用风格包，produce 开拍提问不列入可选清单，`tools/route-style.py` 也不扫描（路由器只看 `styles/` 下无 `_` 前缀且带 `capability.json` 的目录）。

当前禁用：

| 包 | 停用于 | 原因 |
|---|---|---|
| `meme-ledger` | 2026-07-28 | 授权频道反差画面驱动的商业机制解说。曾在 `8d38e26`（PR #12）以 candidate 身份被移进 `styles/`，但包本身还没打磨完（issue #15 的成熟度口径统一也是用户拍板暂缓的）。用户决定退回禁用区，打磨完再谈复活。摘下来的两道路由考题原文存在包内 `routing-cases.parked.json`。 |

复活即：`mv styles/_disabled/<pack> styles/<pack>`，恢复能力卡 `mv capability.parked.json capability.json` 并**复核其 `status` 等字段仍然属实**（路由能力卡规格见 `styles/routing.md` §2）+ 在 `styles/routing-cases.json` 加考题，跑 `python3 tools/route-style.py --check` 全绿，并在 `.claude/skills/produce/SKILL.md` §1.3 可用包清单加回。**能力卡在禁用区一律带 `.parked` 后缀停牌**（2026-07-28 起）：裸 `mv` 回 `styles/` 的包没有 `capability.json`，路由回归会直接失败——这是故意的，防止半成品悄悄进路由；此前卡是活的，这道锁形同虚设。
