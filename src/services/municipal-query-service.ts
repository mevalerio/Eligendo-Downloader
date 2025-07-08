import { MunicipalElectionData } from '../types';
import { readFromFile } from '../utils/file-manager';

export interface MunicipalQuery {
    municipalityName: string;
    date: string;
}

export interface MunicipalQueryResult {
    found: boolean;
    municipality?: {
        municipalityId: string;
        municipalityName: string;
        province: string;
        region: string;
        electionDate: string;
        totalVoters: number;
        totalVotes: number;
        turnout: number;
        parties: Array<{
            partyId: string;
            partyName: string;
            votes: number;
            percentage: number;
            position: number;
            candidates?: Array<{
                candidateId: string;
                candidateName: string;
                votes: number;
            }>;
        }>;
    };
    error?: string;
}

export class MunicipalQueryService {
    private electionDataCache: Map<string, MunicipalElectionData> = new Map();

    // Query results for a specific municipality and date
    async queryMunicipality(municipalityName: string, date: string): Promise<MunicipalQueryResult> {
        try {
            // Normalize inputs
            const normalizedMunicipalityName = municipalityName.toLowerCase().trim();
            const normalizedDate = date.trim();

            // Try to load election data for the specified date
            const electionData = await this.loadElectionData(normalizedDate);
            
            if (!electionData) {
                return {
                    found: false,
                    error: `No election data found for date: ${date}`
                };
            }

            // Search for the municipality
            const municipality = electionData.municipalities.find(muni => 
                muni.municipalityName.toLowerCase() === normalizedMunicipalityName ||
                muni.municipalityName.toLowerCase().includes(normalizedMunicipalityName) ||
                normalizedMunicipalityName.includes(muni.municipalityName.toLowerCase())
            );

            if (!municipality) {
                const availableMunicipalities = electionData.municipalities.map(m => m.municipalityName).join(', ');
                return {
                    found: false,
                    error: `Municipality "${municipalityName}" not found for date ${date}. Available municipalities: ${availableMunicipalities}`
                };
            }

            // Sort parties by votes (highest first) and add position
            const sortedParties = municipality.parties
                .map((party, index) => ({ ...party, originalIndex: index }))
                .sort((a, b) => b.votes - a.votes)
                .map((party, index) => ({
                    partyId: party.partyId,
                    partyName: party.partyName,
                    votes: party.votes,
                    percentage: party.percentage,
                    position: index + 1,
                    candidates: party.candidates
                }));

            return {
                found: true,
                municipality: {
                    municipalityId: municipality.municipalityId,
                    municipalityName: municipality.municipalityName,
                    province: municipality.province,
                    region: municipality.region,
                    electionDate: electionData.electionDate,
                    totalVoters: municipality.totalVoters,
                    totalVotes: municipality.totalVotes,
                    turnout: municipality.turnout,
                    parties: sortedParties
                }
            };

        } catch (error) {
            return {
                found: false,
                error: `Error querying municipality: ${error instanceof Error ? error.message : 'Unknown error'}`
            };
        }
    }

    // Search for municipalities that match a partial name
    async searchMunicipalities(partialName: string, date?: string): Promise<string[]> {
        try {
            const normalizedSearch = partialName.toLowerCase().trim();
            const electionData = await this.loadElectionData(date || '2024-06-08');
            
            if (!electionData) {
                return [];
            }

            return electionData.municipalities
                .filter(muni => 
                    muni.municipalityName.toLowerCase().includes(normalizedSearch) ||
                    muni.province.toLowerCase().includes(normalizedSearch) ||
                    muni.region.toLowerCase().includes(normalizedSearch)
                )
                .map(muni => `${muni.municipalityName} (${muni.province}, ${muni.region})`)
                .sort();

        } catch (error) {
            console.error('Error searching municipalities:', error);
            return [];
        }
    }

    // Get all available election dates
    async getAvailableDates(): Promise<string[]> {
        try {
            // In a real implementation, this would scan available data files
            // For now, return known dates from our demo data
            return ['2024-06-08', '2024-07-08'];
        } catch (error) {
            console.error('Error getting available dates:', error);
            return [];
        }
    }

    // Load election data for a specific date
    private async loadElectionData(date: string): Promise<MunicipalElectionData | null> {
        try {
            const cacheKey = `election-${date}`;
            
            if (this.electionDataCache.has(cacheKey)) {
                return this.electionDataCache.get(cacheKey)!;
            }

            // Try different file naming patterns
            const possibleFileNames = [
                `municipal-election-data-${date}.json`,
                `municipal-election-data.json`,
                `election-data-${date}.json`,
                `election-data.json`
            ];

            for (const fileName of possibleFileNames) {
                try {
                    const data = await readFromFile(fileName) as MunicipalElectionData;
                    if (data && data.electionDate === date) {
                        this.electionDataCache.set(cacheKey, data);
                        return data;
                    }
                } catch (fileError) {
                    // File doesn't exist, try next one
                    continue;
                }
            }

            // If no specific date file found, try loading the default municipal data
            // and check if it matches the requested date
            try {
                const defaultData = await readFromFile('municipal-election-data.json') as MunicipalElectionData;
                if (defaultData) {
                    this.electionDataCache.set(cacheKey, defaultData);
                    return defaultData;
                }
            } catch (error) {
                // Default file doesn't exist
            }

            return null;

        } catch (error) {
            console.error(`Error loading election data for date ${date}:`, error);
            return null;
        }
    }

    // Clear the cache (useful for testing or when data is updated)
    clearCache(): void {
        this.electionDataCache.clear();
    }
}
