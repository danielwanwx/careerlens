# CareerLens 推广调研与 30 天执行方案

更新日期：2026-08-29  
对象：<https://github.com/example-org/careerlens>

## 1. 结论先行

CareerLens 现在不应该按“又一个 AI 简历工具”推广。这个市场拥挤，而且会把项目拖入 ATS 打分、润色和模板生成的同质化竞争。更准确、也更有辨识度的定位是：

> CareerLens turns candidate evidence and target-role sources into an auditable career diagnosis and preparation plan—without inventing experience.

中文：

> CareerLens 把候选人的真实经历和目标岗位证据，转成可审计的职业诊断与准备计划，并明确禁止虚构经历。

首批用户也不应是“所有求职者”，而应聚焦两类人：

1. 已经使用 Codex/agent skills 的技术求职者，尤其是 Senior SDE、AI Platform、Data Platform、Agentic Engineering 方向。
2. 愿意提供完整简历、岗位样本和反馈的高意愿求职者；他们能验证输出是否真的可执行。

推广顺序应为：先补齐转化基础与真实案例，再做小范围验证，随后发布技术型内容和 Show HN；Product Hunt 暂缓。30 天的核心目标不是 star 数，而是 **10 个真实输入、5 个完整有效产物、3 个用户愿意再次使用或推荐**。

## 2. 当前状态与增长瓶颈

截至 2026-08-29，GitHub API 显示仓库公开、Apache-2.0、Python 项目，但为 0 stars、0 forks、0 issues、0 topics；没有 homepage、Releases、Discussions 或 GitHub Pages。仓库已经有 README、schema、样例 JSON、校验器、渲染器、测试和 CI，这说明“可验证的工程骨架”存在，但陌生用户还看不到使用后的价值。

主要断点：

- **发现断点**：没有 GitHub topics，搜索入口几乎为空。
- **理解断点**：README 没有首屏结果图、90 秒演示或“输入 → 诊断 → 准备计划”的视觉证据。
- **安装断点**：缺少一条可复制的一键安装命令或版本化 release 包。
- **信任断点**：没有匿名真实案例、输出前后对比、限制说明的可视化呈现。
- **反馈断点**：没有 issue templates、Discussion 入口或清晰的案例提交方式。

因此，当前直接去大范围发帖，最可能得到浏览和少量 stars，而不是安装与有效使用。

## 3. 市场位置与竞品边界

CareerLens 面临三类替代品：

| 类别 | 用户已有选择 | CareerLens 不应竞争的点 | 应突出差异 |
|---|---|---|---|
| AI 简历润色/ATS 工具 | 关键词匹配、改写、模板、评分 | “更高 ATS 分”或泛化润色 | 证据边界、来源追溯、缺口披露 |
| 面试学习清单 | 算法题单、系统设计课程、通用 roadmap | 资源数量与百科全书式覆盖 | 从个人证据和目标岗位反推优先级 |
| Agent skill 仓库 | 大量通用技能集合 | 技能数量 | 单一任务的深度、schema、质量门、可重复验证 |

竞争不是“谁能生成更多内容”，而是“谁能把事实、推断和待验证项分开，并让用户知道下一步做什么”。仓库内容应该反复证明以下四点：

1. 不虚构候选人经历。
2. 目标岗位结论有来源、有日期、有置信度。
3. 输出不仅是诊断，还有按优先级组织的准备计划。
4. 结果通过 schema 与质量门校验，可重复生成和审阅。

## 4. 渠道优先级

### P0：仓库内转化基础

先完成这些资产，再引流：

1. README 首屏加入一张真实产物截图或 30–90 秒 GIF。
2. 提供一条安装命令，并说明支持的 Codex 环境和最短首次运行路径。
3. 新增三个“输入 → 输出 → 为什么有用”案例：技术岗、非技术岗、薄输入/证据不足。
4. 建立 `v0.1.0` release，提供可下载 zip、变更说明和校验命令。GitHub Releases 本身支持打包软件、release notes 和可下载文件。
5. 设置不超过 20 个准确 topics。建议首批：`codex`、`agent-skills`、`career-planning`、`interview-preparation`、`resume-analysis`、`job-search`、`career-coaching`、`evidence-based`、`python`。
6. 设置 social preview，避免 LinkedIn、X、Slack 分享时只显示空白仓库卡片。
7. 增加两个 issue templates：`Share a validated run`、`Report an evidence or schema problem`。

GitHub 官方说明 topics 会进入 topic 页面和搜索，并帮助用户发现可贡献项目；最多可设置 20 个。因此 topics 是必要的基础设施，但不是独立增长策略。

### P0：封闭验证群

邀请 8–12 人，不公开撒网：

- 4–5 名 Senior/Staff 软件工程师或 AI/Data Platform 求职者；
- 2–3 名跨方向求职者，用于验证通用性；
- 2 名 recruiter、career coach 或 hiring manager，只评审诊断的可信度和可读性。

每位测试者完成同一流程：安装、首次运行、检查证据映射、选择一项准备任务、提交结构化反馈。记录：首次有效产物耗时、失败步骤、人工修复次数、最有价值的一个结论、最不可信的一项。

开放推广门槛：10 人中至少 6 人独立完成安装，至少 5 人在 15 分钟内得到通过校验的产物，且没有严重的履历虚构或来源错配。

### P1：LinkedIn 创始人叙事

第一篇不要写“我发布了一个开源项目，欢迎 star”。应写一个具体问题：通用 AI 职业建议为什么会把事实、推断和想象混在一起，以及 CareerLens 如何用 schema 和 evidence policy 解决它。附 45–60 秒演示和一个匿名案例，结尾只给一个动作：“用你的简历跑一次，并告诉我哪条判断缺少证据。”

后续三篇分别讲：

1. 一个真实案例的诊断前后差异；
2. 如何设计 evidence-bounded agent skill；
3. 首批 10 次运行中哪些假设失败、如何修复。

这比重复发布链接更容易积累可信度，也能同时触达求职者和 agent 开发者。

### P1：Show HN

Show HN 很适合“可运行、有技术设计、作者可现场回答”的开源项目。官方要求用户能实际试用，最好不需要注册或留下邮箱；标题以 `Show HN` 开头；作者应留在评论区交流；不得发动朋友集中点赞或评论。

发布前必须满足：一条安装命令、公开 sample input、可验证 output、短演示、作者至少预留半天回答。建议标题：

> Show HN: CareerLens – an evidence-bounded career diagnosis skill for Codex

首段只回答三个问题：它解决什么、为什么现有通用模型不够、怎样在 5 分钟内试用。不要把帖子写成品牌宣传稿。

### P1：OpenAI/Codex 开发者生态

OpenAI 官方资料确认 Skills API 支持创建、列出、获取、更新和版本化 skill，也确认 plugin 可以包含 skills、MCP 和可选 UI。但本次没有找到官方的第三方公共 skill marketplace 提交流程。因此可以：

- 在 README 中采用标准 skill 目录结构和可复制安装方式；
- 在 OpenAI Developer Community 发布技术复盘或请求反馈，但先核对具体板块规则；
- 未来考虑把 CareerLens 包装成 plugin 或可上传的 skill bundle。

不能宣传为“已上架 OpenAI skill marketplace”，除非以后有明确官方入口并实际通过。

### P2：DEV / Hashnode 技术文章

适合发布完整技术拆解，而不是链接摘要。DEV 的内容政策要求文章本身有实质内容，不能主要为了推广或 backlinks；其社区准则强调 information over promotion。因此正文应公开：evidence taxonomy、schema 设计、一个失败案例、校验器和可复用方法，仓库链接放在自然位置。

建议题目：

> Building an evidence-bounded career agent: separating facts, inferences, and preparation gaps

Hashnode 可以同步，但设定 canonical URL，避免维护两套不同文章。该渠道的目标是搜索沉淀和开发者反馈，不是首日流量。

### P2：Reddit

Reddit 只适合价值先行、逐社区合规的测试，不适合多板块复制同一发布文。Reddit 官方说明推广内容不天然等于 spam，但各社区可完全禁止，也可能采用 10% 自推广规则；重复群发、批量私信和自动化曝光均可能构成 spam。

执行要求：发布前逐一读 subreddit rules；若不明确就联系 moderator；帖子必须包含完整案例或方法，而不是只有 GitHub 链接；一次只测试一个社区和一种叙事，至少间隔数日。优先寻找允许 `Showcase`、`Side Project`、`Feedback` 的技术社区，不把求职焦虑社区当获客池。

### 暂缓：Product Hunt

Product Hunt 允许 maker 自己发布，不需要 Hunter；正式提交需要直接产品 URL、简短 tagline、topics、方形图标、至少两张 gallery 图、描述、maker 和首条评论。它的 featured guidelines 强调有用、创新、完成度和可直接使用的产品，同时明确排除 templates、boilerplates、reports、directories/lists 等类别。

当前 CareerLens 是 GitHub skill + schema + renderer，容易被理解为模板或资源包，而不是独立可体验产品。等到具备交互 demo、一键运行或 hosted playground、真实案例和视觉素材后，再考虑 Product Hunt。现在投入发布素材的机会成本高于预期转化。

## 5. 30 天执行计划

### 第 1 周：让陌生用户能理解并成功运行

- 补齐首屏结果图、演示 GIF、一键安装、Quickstart、三个案例。
- 发布 `v0.1.0`，加入 topics、social preview、issue templates。
- 定义埋点表，不采集用户简历正文，只记录匿名漏斗事件。
- 招募首批 8–12 名测试者。

验收：维护者之外的 3 人能只看 README 独立完成首次运行。

### 第 2 周：证明价值，而不是扩大曝光

- 完成至少 10 次真实测试。
- 修复影响首次成功的前三个问题。
- 取得 2–3 个可公开的匿名案例和一句自然评价。
- 写第一篇 LinkedIn case study，并准备 DEV 长文。

验收：至少 5 个通过校验的真实产物；记录首次产物中位耗时。

### 第 3 周：面向开发者发布

- 发布 LinkedIn 技术案例，48 小时后发布不同角度的 DEV 长文。
- 准备并发布 Show HN；当天集中回答问题，不操纵投票。
- 向 1–2 个高度相关 awesome list 提交合规 PR；提交前完整阅读各仓库贡献规则，不批量投递。

验收：至少 10 次非维护者安装或 clone 后运行，3 个有内容的反馈/issue。

### 第 4 周：复盘并决定是否产品化

- 分析渠道到有效运行的转化，而不是只看 impressions。
- 更新 README 中最常见的失败路径。
- 发布“我们从 20 次运行学到了什么”。
- 若 activation 达标，设计 hosted demo/plugin；否则继续修复 onboarding，不上 Product Hunt。

## 6. 指标与实验设计

### 北极星指标

`Validated Example Run`：非维护者使用自己的或公开样例输入，生成通过 schema/quality gates 的完整产物，并确认至少一项结论或准备行动有价值。

### 漏斗

| 阶段 | 指标 | 30 天最低目标 |
|---|---|---:|
| 发现 | GitHub unique visitors / 内容访问 | 用于诊断，不设虚荣目标 |
| 意向 | unique cloners、release downloads | 30 |
| 激活 | 首次通过校验的产物 | 15 |
| 价值 | 用户确认至少一项可执行结论 | 10 |
| 留存 | 7 天内为第二个岗位或第二位用户重跑 | 3 |
| 贡献 | 有复现信息的 issue、PR 或案例 | 5 |

Stars 只作为社会证明的辅助指标。它无法证明安装、运行或职业结果。

### 三个优先实验

1. **价值主张**：`evidence-bounded career diagnosis` 对比 `personalized career preparation`。同样内容与同样受众，只比较 README 安装点击和有效运行。
2. **首屏证据**：结果截图/GIF 对比纯文字架构说明。观察从访问到 clone/install 的变化。
3. **人群聚焦**：Senior SDE/AI Platform 案例对比通用求职案例。观察有效运行率，不以 impressions 判断。

样本很小时不要宣称统计显著；把结果当方向信号并记录原始计数。

### 停止规则

- 10 名受邀测试者中少于 3 人独立完成：暂停外部推广，重做安装和 Quickstart。
- 超过 20% 产物需要人工修复 schema：先简化输入/生成契约。
- 有流量但 clone/install 转化低于 5%：优先修定位、首屏演示和 CTA。
- 有安装但没有有效产物：这是产品激活问题，不应通过增加发帖掩盖。
- 出现任何履历虚构或来源错配：立即暂停案例传播，修复质量门并补回归测试。

## 7. 可直接使用的文案草案

GitHub description：

> Evidence-bounded career diagnosis and interview preparation for Codex—grounded in candidate facts and target-role sources.

README hero：

> Turn a resume and target-role evidence into an auditable diagnosis and preparation plan. CareerLens separates facts, inferences, and unknowns so it can recommend what to do next without inventing experience.

LinkedIn 开头：

> Most AI career advice has a provenance problem. It mixes what a candidate actually did, what a job posting asks for, and what the model merely assumes. I built CareerLens to keep those three things separate—and to turn the result into a preparation plan that can be reviewed, validated, and corrected.

封闭测试邀请：

> I’m testing an open-source Codex skill that turns a resume plus target-job evidence into a source-backed career diagnosis and preparation plan. I’m looking for 10 people willing to run it once and identify any unsupported conclusion. This is product validation, not a request for stars; please do not share sensitive resume data publicly.

## 8. 本次调研的证据与限制

已核对的一手来源：

- [GitHub：使用 topics 分类仓库](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics?apiVersion=2022-11-28)
- [GitHub：发现项目](https://docs.github.com/en/get-started/exploring-projects-on-github/discovering-projects-on-github)
- [GitHub：Releases](https://docs.github.com/en/repositories/releasing-projects-on-github?apiVersion=2022-11-28)
- [Show HN 官方指南](https://news.ycombinator.com/showhn.html)
- [Product Hunt：如何发布产品](https://help.producthunt.com/en/articles/479557-how-to-post-a-product)
- [Product Hunt：Featured guidelines](https://help.producthunt.com/en/articles/9883485-product-hunt-featuring-guidelines)
- [Product Hunt：Maker forum guide](https://help.producthunt.com/en/articles/11432379-maker-s-guide-to-product-forums)
- [OpenAI：Skills API reference](https://developers.openai.com/api/reference/python/resources/skills/methods/create)
- [OpenAI Developers](https://developers.openai.com/)
- [DEV Content Policy](https://dev.to/terms)
- [DEV：Information over promotion](https://dev.to/devteam/community-moderation-and-support-on-dev-7me)
- [Reddit Spam Policy](https://support.reddithelp.com/hc/en-us/articles/360043504051-Spam)
- [Reddit：社区中的自推广规则](https://support.reddithelp.com/hc/en-us/articles/28012014962580-How-do-I-keep-spam-out-of-my-community)
- [CareerLens GitHub API repository record](https://api.github.com/repos/example-org/careerlens)

Research Engine runs are local-only and configured through `CAREERLENS_RESEARCH_RUN_DIR`. The referenced aggregation run returned `failed_no_rows`: GitHub public search returned an HTTP error, browser recovery required interactive authentication, and the other queries produced no eligible rows. It did not contribute market evidence; this report does not interpret “zero rows” as “no competitors” or “no demand.”

本报告中的渠道排序、30 天目标和停止规则是基于官方平台规则、当前仓库状态与早期项目增长逻辑形成的策略判断，不是平台保证，也不是统计预测。LinkedIn、Hashnode、具体 subreddit 和 awesome list 的实时分发效果与社区规则仍需在实际发布当天复核。
