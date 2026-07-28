# styles/_disabled/ — 暂禁用的风格包

此目录下的包**未完成、暂不 offer 给生产**。`_` 前缀 = 非在用风格包，produce 开拍提问不列入可选清单，`tools/route-style.py` 也不扫描（路由器只看 `styles/` 下无 `_` 前缀且带 `capability.json` 的目录）。

当前没有禁用风格包。

复活即：`mv styles/_disabled/<pack> styles/<pack>`，补 `capability.json`（路由能力卡，见 `styles/routing.md` §2）+ 在 `styles/routing-cases.json` 加考题，跑 `python3 tools/route-style.py --check` 全绿，并在 `.claude/skills/produce/SKILL.md` §1.3 可用包清单加回。**没有能力卡的包移回 `styles/` 会直接让路由回归失败**——这是故意的，防止半成品悄悄进路由。
