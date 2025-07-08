export type ElectionData = {
    electionId: string;
    electionDate: string;
    candidates: Array<{
        id: string;
        name: string;
        party: string;
    }>;
    results: Array<{
        candidateId: string;
        votes: number;
    }>;
};

export type MunicipalElectionData = {
    electionId: string;
    electionDate: string;
    electionType: 'municipal' | 'regional' | 'national';
    municipalities: Array<{
        municipalityId: string;
        municipalityName: string;
        province: string;
        region: string;
        totalVoters: number;
        totalVotes: number;
        turnout: number;
        parties: Array<{
            partyId: string;
            partyName: string;
            votes: number;
            percentage: number;
            candidates?: Array<{
                candidateId: string;
                candidateName: string;
                votes: number;
            }>;
        }>;
    }>;
    summary: {
        totalMunicipalities: number;
        totalVotes: number;
        avgTurnout: number;
        partyTotals: Array<{
            partyId: string;
            partyName: string;
            totalVotes: number;
            percentage: number;
            municipalitiesWon: number;
        }>;
    };
};

export type ApiResponse<T> = {
    data: T;
    status: string;
    message?: string;
};

export type Config = {
    apiUrl: string;
    apiKey: string;
};