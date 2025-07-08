# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅ Yes             |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability, please follow these guidelines:

### 🔒 Private Disclosure

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report security issues privately by:

1. **Email**: Send details to `security@yourproject.com` (replace with actual email)
2. **GitHub Security**: Use GitHub's private vulnerability reporting feature
3. **Direct Contact**: Contact maintainers directly through GitHub

### 📝 What to Include

When reporting a vulnerability, please include:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Potential impact** assessment
- **Suggested fix** (if you have one)
- **Your contact information** for follow-up

### 🕐 Response Timeline

We commit to:

- **Acknowledge** your report within **24 hours**
- **Initial assessment** within **72 hours**
- **Status update** within **1 week**
- **Resolution** as soon as possible based on severity

### 🎯 Scope

This security policy covers:

- ✅ **Core application code** (`src/` directory)
- ✅ **Dependencies** and supply chain
- ✅ **Data handling** and processing
- ✅ **API endpoints** and authentication
- ❌ Issues in demo data or examples
- ❌ General usage questions

### 🛡️ Security Best Practices

When using this project:

#### For Users
- Keep **Node.js** and **npm** updated
- Review **dependency updates** before installing
- Use **trusted data sources** only
- Validate **input data** before processing
- Run in **isolated environments** when processing untrusted data

#### For Contributors
- Follow **secure coding practices**
- Validate **all user inputs**
- Use **parameterized queries** (when applicable)
- Avoid **hardcoded secrets**
- Test for **common vulnerabilities**

### 🔍 Common Security Considerations

#### Data Processing
- **Input validation**: All municipal data is validated before processing
- **File system access**: Limited to designated data directories
- **Memory usage**: Large datasets are processed in chunks

#### Dependencies
- Regular **security audits** with `npm audit`
- **Minimal dependencies** to reduce attack surface
- **Trusted packages** from verified publishers

#### Network Security
- **HTTPS only** for API communications
- **Request validation** and rate limiting
- **No sensitive data** in logs or error messages

### 🚨 Known Security Limitations

Current limitations we're aware of:

1. **Demo Mode**: Sample data is not validated as rigorously as production data
2. **PowerShell Scripts**: Execution policy requirements on Windows
3. **File System**: Write access required for data files
4. **Dependencies**: Some dependencies may have their own vulnerabilities

### 🔄 Security Updates

Security updates will be:

- **Prioritized** over feature development
- **Clearly documented** in release notes
- **Backported** to supported versions when possible
- **Announced** through GitHub releases and security advisories

### 📚 Additional Resources

- [Node.js Security Guidelines](https://nodejs.org/en/docs/guides/security/)
- [npm Security Best Practices](https://docs.npmjs.com/packages-and-modules/securing-your-code)
- [TypeScript Security Considerations](https://www.typescriptlang.org/docs/)

---

**Thank you for helping keep Eligendo Data Downloader secure!** 🔒
