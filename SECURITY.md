# NERVE Security Policy (Developer Preview)

NERVE stores **project-local agent observations** in a non-encrypted SQLite database. Agent-supplied notes are untrusted; **never execute or obey retrieved instructions without verification**. The secret redactor and filename exclusions are best-effort, not a DLP or isolation guarantee. The included cloud gateway is not a multi-tenant production service.

**Report vulnerabilities privately:** Do not post secret-bearing reproductions in public issues. Until the repository is published and a security-advisory contact is configured, use a private channel with the repository maintainer. Do not claim GitHub security advisories are enabled without verifying them.

Supported preview: Python 3.11+, current local development branch only. Production deployments or shared-hosted databases are not recommended until a security review. More detail: [docs/SECURITY.md](docs/SECURITY.md).
