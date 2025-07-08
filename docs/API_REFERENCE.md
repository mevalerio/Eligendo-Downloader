# API Reference

## MunicipalQueryService

The main service class for querying municipal election data.

### Constructor

```typescript
new MunicipalQueryService(filePath?: string)
```

- `filePath`: Optional path to the municipal data JSON file. Defaults to `data/municipal-election-data.json`

### Methods

#### `searchMunicipalities(name: string): MunicipalElectionData[]`

Search for municipalities by name (case-insensitive, partial matching).

**Parameters:**
- `name`: The municipality name to search for

**Returns:** Array of matching municipal election data

**Example:**
```typescript
const service = new MunicipalQueryService();
const results = service.searchMunicipalities("Milano");
```

#### `getMunicipalityResults(name: string, date?: string): MunicipalElectionData[]`

Get election results for a specific municipality, optionally filtered by date.

**Parameters:**
- `name`: The municipality name
- `date`: Optional date filter (YYYY-MM-DD format)

**Returns:** Array of matching municipal election data

#### `getByProvince(province: string): MunicipalElectionData[]`

Get all municipalities in a specific province.

**Parameters:**
- `province`: The province name

**Returns:** Array of municipal election data for the province

#### `getByRegion(region: string): MunicipalElectionData[]`

Get all municipalities in a specific region.

**Parameters:**
- `region`: The region name

**Returns:** Array of municipal election data for the region

#### `getWinningParty(municipalityName: string): string | null`

Get the winning party for a municipality.

**Parameters:**
- `municipalityName`: The municipality name

**Returns:** The name of the winning party or null if not found

## EligendoMunicipalAPI

High-level API for accessing municipal election data.

### Methods

#### `getMunicipalityResults(name: string, date?: string): Promise<MunicipalElectionData[]>`

Get election results for a municipality.

#### `getPartyResults(municipalityName: string, partyName: string): Promise<any>`

Get specific party results for a municipality.

#### `getWinningParty(municipalityName: string): Promise<string | null>`

Get the winning party for a municipality.

#### `searchMunicipalities(searchTerm: string): Promise<MunicipalElectionData[]>`

Search for municipalities by name.

## Data Types

### MunicipalElectionData

```typescript
interface MunicipalElectionData {
  municipality: string;
  province: string;
  region: string;
  date: string;
  totalVoters: number;
  validVotes: number;
  turnoutPercentage: number;
  parties: Party[];
  winner: string;
  summary: {
    totalCandidates: number;
    averageVotePercentage: number;
    marginOfVictory: number;
  };
}
```

### Party

```typescript
interface Party {
  name: string;
  candidates: Candidate[];
  totalVotes: number;
  percentage: number;
  position: number;
}
```

### Candidate

```typescript
interface Candidate {
  name: string;
  votes: number;
  percentage: number;
}
```
