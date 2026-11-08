# Publish NERVE after creating an empty GitHub repository

**Do not paste access tokens into ChatGPT or commit them to Git.** On GitHub, create a new **empty** repository under your account (`NERVE`, preferably public after inspection) without auto-creating README or .gitignore, and grant your chosen GitHub client only the repository permissions it needs.

Then, from the **source root of this package** (not the parent with your own private project database):

```bash
git init
git branch -M main
git add .
git status --short                 # inspect! .nerve/ and secrets must be absent
git commit -m "Prepare NERVE v0.8 local-first release candidate"
git remote add origin https://github.com/OWNER/NERVE.git  # replace OWNER
git push -u origin main
```

Set the About description and topics from [docs/DISCOVERABILITY.md](docs/DISCOVERABILITY.md), then inspect Actions before tagging a preview release and attaching the ZIP/wheel and SHA256 checksums. These commands are **not executed against your GitHub account by this package**.
