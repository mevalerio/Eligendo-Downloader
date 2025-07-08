# Contributing to Eligendo Data Downloader

We welcome contributions to the Eligendo Data Downloader project! This document provides guidelines for contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** for your changes
4. **Make your changes** following our guidelines
5. **Test your changes** thoroughly
6. **Submit a pull request**

## Development Setup

### Prerequisites

- Node.js 16.x or higher
- TypeScript 4.4+
- Git

### Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/eligendo-data-downloader.git
cd eligendo-data-downloader

# Install dependencies
npm install

# Build the project
npm run build

# Run tests
npm test
```

## Code Style Guidelines

### TypeScript

- Use **TypeScript** for all new code
- Follow **strict type checking**
- Use **interfaces** for data structures
- Add **JSDoc comments** for public methods

### Formatting

- Use **2 spaces** for indentation
- Use **single quotes** for strings
- Add **trailing commas** in objects and arrays
- Keep **line length under 100 characters**

### Example:

```typescript
/**
 * Searches for municipalities by name
 * @param name The municipality name to search for
 * @returns Array of matching municipal data
 */
public searchMunicipalities(name: string): MunicipalElectionData[] {
  const searchTerm = name.toLowerCase().trim();
  
  return this.data.filter(municipality => 
    municipality.municipality.toLowerCase().includes(searchTerm)
  );
}
```

## Testing Guidelines

### Unit Tests

- Write tests for **all new functions**
- Use **Jest** testing framework
- Place tests in `__tests__` directories
- Follow the **AAA pattern** (Arrange, Act, Assert)

### Test Example:

```typescript
describe('MunicipalQueryService', () => {
  it('should find Milano when searching for "milano"', () => {
    // Arrange
    const service = new MunicipalQueryService();
    
    // Act
    const results = service.searchMunicipalities('milano');
    
    // Assert
    expect(results).toHaveLength(1);
    expect(results[0].municipality).toBe('Milano');
  });
});
```

### Integration Tests

- Test **end-to-end workflows**
- Verify **API responses**
- Test **PowerShell scripts**

## Documentation Guidelines

### Code Documentation

- Add **JSDoc comments** to all public methods
- Include **parameter descriptions**
- Provide **usage examples**
- Document **return types**

### README Updates

When adding new features:

- Update the **features list**
- Add **usage examples**
- Update the **API reference**
- Include **screenshots** if applicable

## Pull Request Guidelines

### Before Submitting

1. **Test your changes** thoroughly
2. **Update documentation** as needed
3. **Add unit tests** for new functionality
4. **Ensure TypeScript compilation** succeeds
5. **Verify PowerShell scripts** work (if modified)

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] TypeScript compilation succeeds
- [ ] All tests pass
- [ ] Documentation updated
- [ ] PowerShell scripts tested (if applicable)
```

### Review Process

1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Testing verification**
4. **Documentation review**

## Issue Guidelines

### Bug Reports

Include:
- **Environment details** (Node.js version, OS)
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Error messages** or logs
- **Sample data** (if applicable)

### Feature Requests

Include:
- **Clear description** of the feature
- **Use case** explanation
- **Proposed implementation** (if any)
- **Alternatives considered**

## Data Contributions

### Adding Municipalities

To add new municipal data:

1. Follow the existing **data structure**
2. Include **all required fields**
3. Verify **data accuracy**
4. Add appropriate **test cases**

### Data Format

```json
{
  "municipality": "CityName",
  "province": "ProvinceName",
  "region": "RegionName",
  "date": "2023-MM-DD",
  "totalVoters": 50000,
  "validVotes": 45000,
  "turnoutPercentage": 90.0,
  "parties": [...],
  "winner": "PartyName",
  "summary": {...}
}
```

## Release Process

### Version Numbering

We follow **Semantic Versioning** (semver):

- **MAJOR.MINOR.PATCH**
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Checklist

1. **Update version** in package.json
2. **Update CHANGELOG.md**
3. **Create release notes**
4. **Tag the release**
5. **Publish to npm** (if applicable)

## Community Guidelines

### Code of Conduct

- Be **respectful** and **inclusive**
- Focus on **constructive feedback**
- Help **newcomers** get started
- Keep discussions **on-topic**

### Communication

- Use **GitHub Issues** for bug reports and feature requests
- Use **GitHub Discussions** for questions and ideas
- Be **clear and concise** in communications
- Provide **context** for your requests

## Getting Help

- **Documentation**: Check docs/ folder
- **Examples**: See README.md usage section
- **Issues**: Search existing GitHub issues
- **Discussions**: Start a GitHub discussion

Thank you for contributing to Eligendo Data Downloader! 🇮🇹
