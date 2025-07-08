# Getting Started Guide

## Installation

### 1. Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js 16.x or higher** - [Download from nodejs.org](https://nodejs.org/)
- **Git** - [Download from git-scm.com](https://git-scm.com/)
- **PowerShell** (Windows) or Terminal (macOS/Linux)

### 2. Clone the Repository

```bash
git clone https://github.com/yourusername/eligendo-data-downloader.git
cd eligendo-data-downloader
```

### 3. Install Dependencies

```bash
npm install
```

### 4. Verify Installation

```bash
npm run build
```

If successful, you should see TypeScript compilation complete without errors.

## Quick Test

### Run the Municipal Demo

```powershell
# Windows PowerShell
.\run-municipal-demo.ps1
```

```bash
# macOS/Linux
npm run start
```

You should see output showing municipal election data for Italian cities.

### Query a Municipality

```powershell
# Windows PowerShell
.\demo-query.ps1 Milano
```

```bash
# macOS/Linux (using Node.js directly)
node -e "
const { EligendoMunicipalAPI } = require('./dist/eligendo-api');
const api = new EligendoMunicipalAPI();
api.getMunicipalityResults('Milano').then(results => {
  console.log(JSON.stringify(results, null, 2));
});
"
```

## Your First Query

### Using PowerShell (Windows)

The easiest way to get started is using the PowerShell interface:

```powershell
# Search for a municipality
.\demo-query.ps1 Roma

# Get winning party
.\demo-query.ps1 Milano winner

# Search by partial name
.\demo-query.ps1 Mil
```

### Using TypeScript API

Create a new file `my-query.ts`:

```typescript
import { MunicipalQueryService } from './src/services/municipal-query-service';

async function main() {
  const service = new MunicipalQueryService();
  
  // Search for Milano
  const results = service.getMunicipalityResults('Milano');
  
  if (results.length > 0) {
    const milano = results[0];
    console.log(`Municipality: ${milano.municipality}`);
    console.log(`Province: ${milano.province}`);
    console.log(`Winner: ${milano.winner}`);
    console.log(`Turnout: ${milano.turnoutPercentage}%`);
  }
}

main();
```

Run it:

```bash
npx ts-node my-query.ts
```

### Using JavaScript (Simple)

For quick scripts, use the simple JavaScript interface:

```javascript
// simple-query.js
const fs = require('fs');

const data = JSON.parse(fs.readFileSync('data/municipal-election-data.json', 'utf8'));
const milano = data.find(m => m.municipality.toLowerCase().includes('milano'));

if (milano) {
  console.log(`🏛️ ${milano.municipality} (${milano.province})`);
  console.log(`📊 Winner: ${milano.winner}`);
  console.log(`🗳️ Turnout: ${milano.turnoutPercentage}%`);
}
```

## Next Steps

1. **Explore the data** - Check out `data/municipal-election-data.json` to see the available municipalities
2. **Read the API documentation** - See `docs/API_REFERENCE.md` for detailed method documentation
3. **Try different queries** - Experiment with province and region filtering
4. **Build your own tools** - Use the TypeScript APIs to create custom analysis tools

## Common Issues

### TypeScript Compilation Errors

If you see TypeScript errors, ensure you have the correct Node.js version:

```bash
node --version  # Should be 16.x or higher
npm --version   # Should be 7.x or higher
```

### PowerShell Execution Policy

On Windows, you might need to enable PowerShell script execution:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Missing Data Files

If queries return empty results, verify the data files exist:

```bash
ls data/
# Should show: demo-election-data.json, municipal-election-data.json
```

## Support

If you encounter issues:

1. Check the [API Reference](API_REFERENCE.md)
2. Review the [examples](../README.md#usage)
3. Open an issue on GitHub
