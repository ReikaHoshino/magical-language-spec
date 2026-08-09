# Security Policy

## Supported scope

Security fixes are evaluated against the current `main` branch and the current released specification identity, v0.12.0. Historical files under `spec/` are immutable records and are not maintained as executable security baselines.

This repository is a reference specification and implementation. It is not authorization for real-world control, production deployment, or unsafe execution. The authority, lease, conservation, sandbox, and fail-closed boundaries in current `reference/` remain normative.

## Reporting a vulnerability

Use GitHub's **Report a vulnerability** private-reporting flow for this repository. Do not include secrets, credentials, private personal information, or exploit material in a public Issue or Pull Request.

Include, when practical:

- the affected commit or released version;
- the relevant input, contract identity, and execution stage;
- a minimal reproduction;
- expected and actual fail-closed behavior;
- potential impact and any known workaround.

If private vulnerability reporting is unavailable, contact the repository owner through a private channel before disclosing sensitive details publicly.

Security reports do not grant Capability, Authority, Lease, admission, or permission to bypass repository safeguards. Please do not test against systems or data you do not own or have explicit permission to use.

## Public disclosure

After a fix is available, the maintainer may publish a concise advisory and credit the reporter if requested. Timing depends on impact, validation, and release coordination.
