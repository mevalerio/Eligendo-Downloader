# Security policy

## Supported version

Security fixes are applied to the latest revision of the default branch. No
separate long-term support series is currently maintained.

## Reporting a vulnerability

Please avoid publishing exploitable details in a public issue. If the GitHub
repository enables private vulnerability reporting, use its **Security >
Advisories > Report a vulnerability** function. Otherwise, contact the
repository owner privately and include:

- the affected revision;
- reproduction steps;
- the expected and observed behaviour; and
- the potential impact.

Do not include credentials, personal data, or downloaded production databases
in a report.

## Deployment note

The URL allow-list and archive checks reduce exposure to untrusted input but do
not replace operating system, container, or network isolation. Review the
configuration and access controls before exposing the API on a public network.
