# Research · openai-78m-logs

> 核实途径：WebSearch 调查（2026-07-16，选题筛选轮已核原文日期）。script 中每个事实主张必须回链编号。
> 时效戳：全部事实核实于 2026-07-16。

- **F01** NYT 在版权诉讼新文件中指控 OpenAI 私下建立约 7800 万条"去标识化"ChatGPT 用户对话数据库用于内部侵权自查，工具集代号 Project Giraffe（含 Bloom 过滤器）。——TechCrunch 2026-07-09：https://techcrunch.com/2026/07/09/new-york-times-says-openai-hid-evidence-in-chatgpt-copyright-trial/
- **F02** 法院此前已裁定 OpenAI 移交 2000 万条 ChatGPT 聊天记录样本用于诉讼取证；NYT 称收到的样本"不可用"。——National Law Review：https://natlawreview.com/article/openai-loses-privacy-gambit-20-million-chatgpt-logs-likely-headed-copyright
- **F03** NYT 同时指控 OpenAI 涉嫌删除数十亿条模型输出，违反证据保全令。——同 F01 来源
- **F04** 《人工智能拟人化互动服务管理暂行办法》2026-04-10 公布，2026-07-15 起施行。——网信办官方全文：https://www.cac.gov.cn/2026-04/10/c_1777558395078289.htm
- **F05** 办法第 16 条：拟人化互动服务的交互数据须采取加密与访问控制措施，未经用户同意不得向第三方提供。——同 F04 官方全文（条款已核）
- **F06** 办法第 17 条：不满 14 周岁未成年人个人信息处理须取得监护人同意，并开展合规审计。——同 F04
- **F07** 办法第 13 条：服务方识别到用户极端情绪时须干预引导。——同 F04（⚠️ 视频中仅作法定义务列举，不展开）
- **F08** 事件热度佐证：TechCrunch、Bloomberg Law、ABA Journal、eWeek、National Law Review 及多家律所博客同周（7/9–7/16）跟进报道。——多源交叉

## 解读点（分析立场，非事实主张，不需回链）

- 去标识化 ≠ 匿名化：7800 万条"去标识"对话仍可整体分析、可能被重识别——这是隐私工程的常识性区分；
- 数据最小化原则：服务商留存远超服务所需的数据本身即风险；
- 密态计算的核心主张：让服务商自己也无法明文读取用户数据——制度（F05）管义务，技术管能力。
