# 🇮🇹 Eligendo Data Downloader

A comprehensive TypeScript-based tool for downloading and analyzing Italian municipal election data from Eligendo.

[![Node.js](https://img.shields.io/badge/Node.js-22.x-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.4+-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/release/mevalerio/Eligendo-Downloader.svg)](https://github.com/mevalerio/Eligendo-Downloader/releases)
[![Build Status](https://github.com/mevalerio/Eligendo-Downloader/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/mevalerio/Eligendo-Downloader/actions)
[![GitHub stars](https://img.shields.io/github/stars/mevalerio/Eligendo-Downloader.svg)](https://github.com/mevalerio/Eligendo-Downloader/stargazers)

## 🌟 Features

- **📊 Municipal Election Data Processing** - Download and parse Italian municipal election results
- **🔍 Advanced Query System** - Query results by municipality name and date
- **🏛️ Geographic Breakdown** - Results organized by Province and Region
- **📈 Statistical Analysis** - Turnout rates, vote percentages, and winner analysis
- **🎯 Multiple Access Methods** - PowerShell scripts, command-line tools, and programmatic API
- **🇮🇹 Italian Municipalities Support** - Built for Italian electoral system

## 🚀 Quick Start

### Prerequisites

- **Node.js 16.x or higher** ([Download here](https://nodejs.org/))
- **Windows** with PowerShell (primary support)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mevalerio/Eligendo-Downloader.git
   cd Eligendo-Downloader
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Verify installation**
   ```powershell
   .\verify-for-publication.ps1
   ```

4. **Run the demo**
   ```powershell
   .\run-municipal-demo.ps1
   ```

## 📖 Usage

### 🏛️ Query Municipal Results

**Get election results for any Italian municipality:**

```powershell
# Query Milano results
.\demo-query.ps1 Milano

# Query Roma with specific date
.\demo-query.ps1 Roma 2024-06-08

# List all available municipalities
.\demo-query.ps1 --list

# Show winners for all cities
.\demo-query.ps1 --winners
```

**Example Output:**
```
🏛️ === MILANO ELECTION RESULTS ===
📍 Location: Milano, Lombardia
👥 Total Voters: 850,000
🗳️ Total Votes: 680,000
📈 Turnout: 80.0%

🎯 PARTY RESULTS:
🥇 1. Partito Democratico
     🗳️ Votes: 272,000 (40.0%)
     👤 Giuseppe Sala: 272,000 votes

🥈 2. Lega
     🗳️ Votes: 204,000 (30.0%)
     👤 Luca Bernardo: 204,000 votes
```

### 🔧 Programmatic API

```typescript
import { EligendoMunicipalAPI } from './src/eligendo-api';

const api = new EligendoMunicipalAPI();

// Get full results for a municipality
const result = await api.getMunicipalityResults('Milano', '2024-06-08');

// Get simplified party results
const parties = await api.getPartyResults('Roma');

// Get winning party
const winner = await api.getWinningParty('Napoli');

// Search municipalities
const cities = await api.searchMunicipalities('mil');
```

### 📊 Available Demo Data

The system includes demo data for major Italian cities:

- **Milano** (Lombardia) - 850,000 voters, 80.0% turnout
- **Roma** (Lazio) - 1,200,000 voters, 75.0% turnout  
- **Napoli** (Campania) - 650,000 voters, 70.0% turnout

## 🏗️ Project Structure

```
eligendo-data-downloader/
├── src/
│   ├── main.ts                    # Main application entry
│   ├── eligendo-api.ts           # Programmatic API
│   ├── municipal-query.ts        # Command-line query tool
│   ├── downloader/
│   │   ├── eligendo-client.ts    # API client for Eligendo
│   │   ├── data-parser.ts        # Basic election data parser
│   │   └── municipal-data-parser.ts # Municipal-level parser
│   ├── services/
│   │   └── municipal-query-service.ts # Core query logic
│   ├── types/
│   │   └── index.ts              # TypeScript type definitions
│   └── utils/
│       ├── file-manager.ts       # File I/O operations
│       └── logger.ts             # Logging utilities
├── data/                         # Generated election data
├── config/                       # Configuration files
├── demo-query.ps1               # PowerShell query interface
├── run-municipal-demo.ps1       # Municipal demo script
└── docs/                        # Documentation
```

## 🎯 Commands Reference

### PowerShell Scripts (Recommended)

| Script | Description |
|--------|-------------|
| `.\demo-query.ps1 <municipality>` | Query specific municipality |
| `.\demo-query.ps1 --list` | Show all municipalities |
| `.\demo-query.ps1 --winners` | Show winners for all cities |
| `.\run-municipal-demo.ps1` | Run complete municipal demo |
| `.\run-demo.ps1` | Run basic candidate demo |

### Command Line Tools

```bash
# Compile TypeScript
npm run build

# Query municipality
node dist/municipal-query.js Milano

# Search municipalities  
node dist/municipal-query.js --search "mil"

# Show available dates
node dist/municipal-query.js --dates
```

### NPM Scripts

```bash
npm start          # Run main application
npm run build      # Compile TypeScript
npm test           # Run tests (if available)
```

## 📊 Data Format

### Municipal Election Data Structure

```json
{
  "electionId": "elezioni-comunali-2024",
  "electionDate": "2024-06-08",
  "electionType": "municipal",
  "municipalities": [
    {
      "municipalityId": "milano",
      "municipalityName": "Milano",
      "province": "Milano",
      "region": "Lombardia",
      "totalVoters": 850000,
      "totalVotes": 680000,
      "turnout": 80.0,
      "parties": [
        {
          "partyId": "pd",
          "partyName": "Partito Democratico",
          "votes": 272000,
          "percentage": 40.0,
          "candidates": [
            {
              "candidateId": "sala-milano",
              "candidateName": "Giuseppe Sala",
              "votes": 272000
            }
          ]
        }
      ]
    }
  ]
}
```

## 🔧 Configuration

### API Configuration (`config/default.json`)

```json
{
  "apiEndpoint": "https://api.eligendo.it/elections",
  "auth": {
    "username": "your_username",
    "password": "your_password"
  },
  "dataFetchInterval": 3600,
  "outputDirectory": "./data",
  "logLevel": "info"
}
```

## 🔌 Real API Integration

To connect to the actual Eligendo API:

1. **Update credentials** in `config/default.json`
2. **Modify API endpoints** in `src/downloader/eligendo-client.ts`
3. **Configure authentication** as required by Eligendo
4. **Run**: `npm start`

## 🧪 Testing

Run the municipal demo to verify everything works:

```powershell
# Test basic functionality
.\run-municipal-demo.ps1

# Test query functionality
.\demo-query.ps1 Milano

# Test with all municipalities
.\demo-query.ps1 --winners
```

## 📝 Documentation

- **[Query Guide](QUERY-GUIDE.md)** - Complete query documentation
- **[Query Examples](QUERY-RESULTS.md)** - Example query results
- **[Working Guide](WORKING.md)** - Setup and troubleshooting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Requirements

- **Node.js** 16.x or higher
- **TypeScript** 4.4 or higher
- **Windows** (primary), Linux/macOS (experimental)
- **PowerShell** (for scripts)

## 🔒 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Eligendo** for providing Italian electoral data
- **Node.js community** for excellent tooling
- **TypeScript team** for type safety

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/eligendo-data-downloader/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/eligendo-data-downloader/discussions)

## 🗺️ Roadmap

- [ ] **Multiple Election Types** - Support for regional and national elections
- [ ] **Real-time Data** - Live election result streaming
- [ ] **Data Visualization** - Built-in charts and graphs
- [ ] **Export Formats** - CSV, Excel, and PDF export
- [ ] **REST API** - HTTP API for external integrations
- [ ] **Docker Support** - Containerized deployment

---

**Made with ❤️ for Italian Democracy** 🇮🇹

## Quick Publish to GitHub

If you want to publish this project to your own GitHub repository:

```powershell
# Run the automated publication script
.\publish-to-github.ps1
```

This script will:
- ✅ Update package.json with your GitHub information
- ✅ Run all pre-publication tests
- ✅ Set up Git repository and create initial commit
- ✅ Provide step-by-step GitHub setup instructions
- ✅ Open GitHub in your browser to create the repository

### Manual Installation