# Claude Code plugins by firas-taiem

Skills and plugins for [Claude Code](https://code.claude.com), packaged so they install with two lines and update on their own. Each plugin has its own folder under `plugins/` with a README that walks through setup step by step.

## Install

**Claude desktop app (no terminal):** open **Customize → Plugins** (or Settings → Plugins), click **+ Add → Add marketplace → Add from a repository**, type `firas-taiem/claude-plugins` in the URL field and click **Sync**. Then open the **Discover** tab and click **Add** on the plugin you want. Type the marketplace name as shown, not a link copied from a GitHub page.

**Claude Code in a terminal:** add this marketplace once, then install any plugin from the list below:

```
/plugin marketplace add firas-taiem/claude-plugins
/plugin install <plugin-name>@firas-taiem
```

Plugins install into your Claude account and work in every folder you open. Skills from a plugin are called as `/<plugin-name>:<skill-name>`.

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
