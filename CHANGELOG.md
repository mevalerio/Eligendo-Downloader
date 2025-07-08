# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-07-08

### Added
- 🇮🇹 Initial release of Eligendo Data Downloader
- 📊 Municipal election data processing for Italian municipalities
- 🔍 Advanced query system with multiple access methods
- 🏛️ Geographic breakdown by Province and Region
- 📈 Statistical analysis with turnout rates and winner calculation
- 🎯 PowerShell scripts for easy command-line access
- 📖 TypeScript API for programmatic access
- 🗂️ Mock Italian election data for Milano, Roma, and Napoli
- 📋 Comprehensive documentation and examples

### Features
- **MunicipalQueryService**: Core service for querying municipal data
- **EligendoMunicipalAPI**: High-level API interface
- **PowerShell Integration**: Native Windows PowerShell support
- **Multiple Query Methods**: Search by name, province, region, date
- **Data Analytics**: Turnout analysis, winner determination, vote percentages
- **TypeScript Support**: Full type safety and IntelliSense
- **Extensible Architecture**: Easy to add new data sources and query types

### Core Components
- `MunicipalQueryService`: Main query engine
- `EligendoClient`: HTTP client for API communications
- `MunicipalDataParser`: Data processing and validation
- `FileManager`: File operations and data persistence
- `Logger`: Comprehensive logging system

### Scripts & Tools
- `demo-query.ps1`: Interactive PowerShell query tool
- `run-municipal-demo.ps1`: Complete demo with sample data
- `simple-query.js`: Lightweight JavaScript interface
- Multiple TypeScript demo files

### Documentation
- Complete API reference
- Getting started guide
- Contributing guidelines
- Query examples and results
- Working documentation

## [Unreleased]

### Planned
- 🌐 Real Eligendo API integration
- 🔄 Data synchronization and caching
- 📊 Advanced analytics and reporting
- 🗺️ Geographic visualization features
- 📱 Web interface for data exploration
- 🔒 Authentication and rate limiting
- 📦 npm package publication
- 🐳 Docker containerization

### Future Enhancements
- Support for regional and national election data
- Historical election data comparison
- Export functionality (CSV, Excel, PDF)
- Real-time election result streaming
- Multi-language support
- REST API server mode
- Integration with Italian government data sources
