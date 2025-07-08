# Development Notes

## Project Structure Overview

This document provides internal development notes and architecture insights for contributors.

### Core Architecture

```
src/
├── main.ts                    # Entry point
├── eligendo-api.ts           # High-level API interface
├── municipal-query.ts        # CLI query interface
├── demo.ts                   # Basic demo
├── municipal-demo.ts         # Municipal-specific demo
├── query-demo.ts            # Query demonstration
├── downloader/              # Data acquisition layer
│   ├── eligendo-client.ts   # HTTP client
│   ├── data-parser.ts       # Generic data parsing
│   └── municipal-data-parser.ts # Municipal-specific parsing
├── services/                # Business logic layer
│   └── municipal-query-service.ts # Query operations
├── types/                   # Type definitions
│   └── index.ts            # Shared types
├── utils/                   # Utilities
│   ├── file-manager.ts     # File operations
│   └── logger.ts           # Logging system
└── models/                  # Data models
    └── election-data.ts     # Election data structures
```

### Data Flow

1. **Input**: Municipality name/query → `MunicipalQueryService`
2. **Processing**: Data loading → Filtering → Validation
3. **Output**: Structured results → Display/Export

### Key Design Decisions

#### TypeScript-First Approach
- **Reasoning**: Type safety for complex election data structures
- **Benefits**: IntelliSense, compile-time error detection
- **Trade-offs**: Additional build step, learning curve

#### PowerShell Integration
- **Reasoning**: Windows-first deployment, easy for non-developers
- **Benefits**: Native OS integration, colored output
- **Trade-offs**: Platform-specific, execution policy requirements

#### Mock Data Strategy
- **Reasoning**: Development without API dependency
- **Benefits**: Consistent testing, offline development
- **Trade-offs**: May not reflect real API structure

### Technical Decisions

#### File Structure
```typescript
// Preferred import pattern
import { MunicipalQueryService } from './services/municipal-query-service';
import { MunicipalElectionData } from './types';

// Avoid deep nesting
import { Logger } from '../../utils/logger'; // ❌
import { Logger } from '../utils/logger';    // ✅
```

#### Error Handling Strategy
```typescript
// Consistent error patterns
try {
  const results = service.query(params);
  return { success: true, data: results };
} catch (error) {
  logger.error('Query failed', error);
  return { success: false, error: error.message };
}
```

#### Data Validation
```typescript
// Input validation at service boundaries
public searchMunicipalities(name: string): MunicipalElectionData[] {
  if (!name || name.trim().length === 0) {
    throw new Error('Municipality name is required');
  }
  // ... rest of method
}
```

### Performance Considerations

#### Data Loading
- **Current**: Load entire dataset into memory
- **Future**: Implement lazy loading for large datasets
- **Memory**: ~1MB for demo data, potentially 100MB+ for full dataset

#### Query Performance
- **Search**: O(n) linear search through municipalities
- **Optimization**: Consider indexing by name/province for O(1) lookup
- **Caching**: Results cached in memory during service lifetime

### Testing Strategy

#### Unit Tests (Planned)
```typescript
// Service layer tests
describe('MunicipalQueryService', () => {
  it('should find exact municipality matches', () => {
    // Test implementation
  });
});

// Data parser tests
describe('MunicipalDataParser', () => {
  it('should validate required fields', () => {
    // Test implementation
  });
});
```

#### Integration Tests (Planned)
- PowerShell script execution
- File system operations
- API endpoint testing (when real API integrated)

### Configuration Management

#### Current Approach
```json
// config/default.json
{
  "dataPath": "data/municipal-election-data.json",
  "logLevel": "info",
  "outputFormat": "json"
}
```

#### Environment Variables (Planned)
```bash
ELIGENDO_API_URL=https://api.eligendo.it
ELIGENDO_DATA_PATH=/custom/path/data.json
ELIGENDO_LOG_LEVEL=debug
```

### Deployment Considerations

#### Build Process
```bash
# TypeScript compilation
npm run build
# Outputs to dist/ directory

# File structure after build
dist/
├── main.js
├── eligendo-api.js
├── types/
└── services/
```

#### Distribution
- **npm package**: For programmatic usage
- **GitHub releases**: For manual download
- **Docker image**: For containerized deployment (planned)

### API Integration Notes

#### Current Mock Structure
```typescript
interface MunicipalElectionData {
  municipality: string;      // "Milano"
  province: string;         // "Milano"
  region: string;          // "Lombardia"
  date: string;           // "2023-06-11"
  // ... rest of structure
}
```

#### Real API Integration (Planned)
```typescript
// Expected Eligendo API endpoint structure
GET /api/v1/municipalities/{id}/elections/{date}
GET /api/v1/elections/search?municipality={name}&date={date}
```

### Code Quality Tools

#### Planned Integrations
- **ESLint**: Code linting and style enforcement
- **Prettier**: Code formatting
- **Husky**: Git hooks for pre-commit checks
- **GitHub Actions**: CI/CD pipeline

#### Current Status
- ✅ TypeScript compilation
- ❌ Linting (planned)
- ❌ Formatting (planned)
- ❌ Testing framework setup (jest configured but no tests)

### Known Technical Debt

1. **Error Handling**: Inconsistent error types across modules
2. **Logging**: Basic console.log, needs structured logging
3. **Configuration**: Hardcoded paths, needs environment variables
4. **Testing**: No test suite implemented yet
5. **Documentation**: API docs need examples and edge cases

### Future Architecture Plans

#### Microservices Approach
```
eligendo-data-downloader/
├── api-service/           # REST API server
├── query-service/         # Core query logic
├── data-service/          # Data management
└── web-interface/         # Frontend application
```

#### Real-time Features
- WebSocket connections for live election updates
- Event-driven architecture for data synchronization
- Caching layer with Redis

### Development Environment

#### Recommended VS Code Extensions
- **TypeScript Importer**: Auto-import management
- **Prettier**: Code formatting
- **ESLint**: Linting
- **PowerShell**: Script development
- **GitLens**: Git integration

#### Debug Configuration
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Main",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/src/main.ts",
      "outFiles": ["${workspaceFolder}/dist/**/*.js"],
      "runtimeArgs": ["-r", "ts-node/register"]
    }
  ]
}
```

---

*This document is updated regularly as the project evolves.*
