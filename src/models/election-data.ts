export interface ElectionData {
    electionId: string;
    electionDate: Date;
    candidates: Array<{
        candidateId: string;
        name: string;
        party: string;
    }>;
    results: Array<{
        candidateId: string;
        votes: number;
    }>;
}