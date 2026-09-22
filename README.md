# Claude Code plugins by firas-taiem

Skills and plugins for [Claude Code](https://code.claude.com), packaged so they install with two lines and update on their own. Each plugin has its own folder under `plugins/` with a README that walks through setup step by step.

## Install

In Claude Code (the desktop app's Code tab, or the terminal), add this marketplace once:

```
/plugin marketplace add firas-taiem/claude-plugins
```

Then install any plugin from the list below:

```
/plugin install <plugin-name>@firas-taiem
```

Or click **+** next to the prompt box, choose **Plugins**, and pick from the list. Plugins install into your Claude account and work in every folder you open. Skills from a plugin are called as `/<plugin-name>:<skill-name>`.

## Plugins

| Plugin | What it does | Setup guide |
|---|---|---|
| **resume-kit** | Tailors your resume to a job posting from your own content only, fact-checks it against your master, waits for your approval, then makes an ATS-safe two-page PDF. | [plugins/resume-kit/README.md](plugins/resume-kit/README.md) |

## Updating

```
/plugin marketplace update firas-taiem
/reload-plugins
```

## Requirements

A Claude Pro, Max, Team or Enterprise plan (Claude Code is not on the free plan). Each plugin's README lists anything else it needs, such as Python or Chrome.

## Layout

```
.claude-plugin/marketplace.json     the catalog Claude Code reads
plugins/
  <plugin-name>/
    .claude-plugin/plugin.json      name, version, description
    README.md                       setup guide for that plugin
    skills/<skill-name>/SKILL.md    the skill, with its scripts beside it
```

## License

MIT. See [LICENSE](LICENSE).
