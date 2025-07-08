import { MunicipalQueryService, MunicipalQueryResult } from './services/municipal-query-service';

// Simple API-style functions for querying municipality data
export class EligendoMunicipalAPI {
    private queryService: MunicipalQueryService;

    constructor() {
        this.queryService = new MunicipalQueryService();
    }

    /**
     * Get election results for a specific municipality and date
     * @param municipalityName - Name of the municipality (e.g., "Milano", "Roma")
     * @param date - Election date in YYYY-MM-DD format (optional, defaults to "2024-06-08")
     * @returns Promise with municipality election results
     */
    async getMunicipalityResults(municipalityName: string, date: string = '2024-06-08'): Promise<MunicipalQueryResult> {
        return await this.queryService.queryMunicipality(municipalityName, date);
    }

    /**
     * Search for municipalities by partial name
     * @param partialName - Partial municipality name to search for
     * @param date - Election date (optional)
     * @returns Promise with array of matching municipality names
     */
    async searchMunicipalities(partialName: string, date?: string): Promise<string[]> {
        return await this.queryService.searchMunicipalities(partialName, date);
    }

    /**
     * Get all available election dates
     * @returns Promise with array of available dates
     */
    async getAvailableDates(): Promise<string[]> {
        return await this.queryService.getAvailableDates();
    }

    /**
     * Get party results for a municipality (simplified format)
     * @param municipalityName - Name of the municipality
     * @param date - Election date (optional)
     * @returns Promise with simplified party results
     */
    async getPartyResults(municipalityName: string, date: string = '2024-06-08'): Promise<{
        municipalityName: string;
        date: string;
        parties: Array<{
            name: string;
            votes: number;
            percentage: number;
            position: number;
        }>;
    } | null> {
        const result = await this.getMunicipalityResults(municipalityName, date);
        
        if (!result.found || !result.municipality) {
            return null;
        }

        return {
            municipalityName: result.municipality.municipalityName,
            date: result.municipality.electionDate,
            parties: result.municipality.parties.map(party => ({
                name: party.partyName,
                votes: party.votes,
                percentage: party.percentage,
                position: party.position
            }))
        };
    }

    /**
     * Get the winning party for a municipality
     * @param municipalityName - Name of the municipality  
     * @param date - Election date (optional)
     * @returns Promise with winning party information
     */
    async getWinningParty(municipalityName: string, date: string = '2024-06-08'): Promise<{
        municipalityName: string;
        winningParty: string;
        votes: number;
        percentage: number;
        margin?: number;
    } | null> {
        const result = await this.getMunicipalityResults(municipalityName, date);
        
        if (!result.found || !result.municipality || result.municipality.parties.length === 0) {
            return null;
        }

        const sortedParties = result.municipality.parties.sort((a, b) => b.votes - a.votes);
        const winner = sortedParties[0];
        const runnerUp = sortedParties[1];
        
        return {
            municipalityName: result.municipality.municipalityName,
            winningParty: winner.partyName,
            votes: winner.votes,
            percentage: winner.percentage,
            margin: runnerUp ? winner.votes - runnerUp.votes : undefined
        };
    }

    /**
     * Clear the internal cache (useful for testing or when data is updated)
     */
    clearCache(): void {
        this.queryService.clearCache();
    }
}

// Example usage functions
export async function quickQuery(municipalityName: string, date?: string): Promise<void> {
    const api = new EligendoMunicipalAPI();
    const result = await api.getMunicipalityResults(municipalityName, date);
    
    if (result.found && result.municipality) {
        console.log(`\n📊 Results for ${result.municipality.municipalityName}:`);
        result.municipality.parties.forEach((party, index) => {
            const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '  ';
            console.log(`${medal} ${party.partyName}: ${party.votes.toLocaleString()} votes (${party.percentage.toFixed(1)}%)`);
        });
    } else {
        console.log(`❌ ${result.error}`);
    }
}

export async function quickWinner(municipalityName: string, date?: string): Promise<void> {
    const api = new EligendoMunicipalAPI();
    const winner = await api.getWinningParty(municipalityName, date);
    
    if (winner) {
        console.log(`🏆 Winner in ${winner.municipalityName}: ${winner.winningParty} with ${winner.votes.toLocaleString()} votes (${winner.percentage.toFixed(1)}%)`);
        if (winner.margin) {
            console.log(`   Margin of victory: ${winner.margin.toLocaleString()} votes`);
        }
    } else {
        console.log(`❌ No results found for ${municipalityName}`);
    }
}
