import { ElectionData } from '../types';

export function parseData(rawData: any): ElectionData {
    const parsedData: ElectionData = {
        electionId: rawData.id,
        electionDate: rawData.date,
        candidates: rawData.candidates.map((candidate: any) => ({
            id: candidate.id,
            name: candidate.name,
            party: candidate.party,
        })),
        results: rawData.results.map((result: any) => ({
            candidateId: result.candidateId,
            votes: result.votes,
        })),
    };

    return parsedData;
}