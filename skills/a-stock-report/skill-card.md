## Description: <br>
Generates and pushes data-driven A-share market reports, including morning reports, close summaries, evening reports, intraday alerts, IPO weekly reports, weekend news, sentiment scoring, and AI market outlook sections. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[cookfish1979](https://clawhub.ai/user/cookfish1979) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and operators use this skill to schedule, generate, save, and send A-share market reports and alerts through WeCom using market data APIs and local cron-style jobs. It is intended for automated financial reporting workflows, not as standalone investment advice. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The release asks agents to read or grep local environment files and broadly loads local credentials for scheduled outbound reporting. <br>
Mitigation: Before enabling cron jobs, remove prompt steps that read or grep `.env`, keep only the required report credentials in the loaded environment, and use a dedicated low-scope WeCom webhook key. <br>
Risk: Scheduled jobs can send generated market reports to an external WeCom webhook. <br>
Mitigation: Install only when scheduled A-share reporting to WeCom is intended, review every configured cron task, and confirm the webhook destination before running. <br>
Risk: The workflow depends on the separate `hithink-sector-selector` skill for sector data. <br>
Mitigation: Trust and scan the referenced skill before enabling reports that depend on sector-selection data. <br>


## Reference(s): <br>
- [ClawHub skill listing](https://clawhub.ai/cookfish1979/a-stock-report) <br>
- [Tencent market data endpoint](https://qt.gtimg.cn/q=sh000300,sz399001) <br>
- [iWenCai OpenAPI](https://openapi.iwencai.com) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown reports, WeCom webhook messages, shell commands, and cron configuration snippets] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Produces scheduled reports and alerts; some report sections depend on an agent-generated intermediate text file before the Python sender scripts run.] <br>

## Skill Version(s): <br>
1.10.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
