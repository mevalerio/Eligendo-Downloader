import { ElectionData, MunicipalElectionData } from '../types';

// Original parser for basic candidate data
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

// Enhanced parser for municipality-level election data
export function parseMunicipalData(rawData: any): MunicipalElectionData {
    const municipalities = rawData.municipalities?.map((muni: any) => ({
        municipalityId: muni.id,
        municipalityName: muni.name,
        province: muni.province,
        region: muni.region,
        totalVoters: muni.totalVoters,
        totalVotes: muni.totalVotes,
        turnout: muni.turnout || (muni.totalVotes / muni.totalVoters * 100),
        parties: muni.parties?.map((party: any) => ({
            partyId: party.id,
            partyName: party.name,
            votes: party.votes,
            percentage: party.percentage || (party.votes / muni.totalVotes * 100),
            candidates: party.candidates?.map((candidate: any) => ({
                candidateId: candidate.id,
                candidateName: candidate.name,
                votes: candidate.votes,
            })) || [],
        })) || [],
    })) || [];    // Calculate summary statistics
    const totalMunicipalities = municipalities.length;
    const totalVotes = municipalities.reduce((sum: number, muni: any) => sum + muni.totalVotes, 0);
    const avgTurnout = municipalities.reduce((sum: number, muni: any) => sum + muni.turnout, 0) / totalMunicipalities;

    // Calculate party totals across all municipalities
    const partyTotalsMap = new Map<string, { name: string; votes: number; municipalitiesWon: number }>();
    
    municipalities.forEach((muni: any) => {
        let winningParty = '';
        let maxVotes = 0;
        
        muni.parties.forEach((party: any) => {
            if (!partyTotalsMap.has(party.partyId)) {
                partyTotalsMap.set(party.partyId, { name: party.partyName, votes: 0, municipalitiesWon: 0 });
            }
            const partyTotal = partyTotalsMap.get(party.partyId)!;
            partyTotal.votes += party.votes;
            
            if (party.votes > maxVotes) {
                maxVotes = party.votes;
                winningParty = party.partyId;
            }
        });
        
        if (winningParty && partyTotalsMap.has(winningParty)) {
            partyTotalsMap.get(winningParty)!.municipalitiesWon++;
        }
    });

    const partyTotals = Array.from(partyTotalsMap.entries()).map(([partyId, data]) => ({
        partyId,
        partyName: data.name,
        totalVotes: data.votes,
        percentage: totalVotes > 0 ? (data.votes / totalVotes * 100) : 0,
        municipalitiesWon: data.municipalitiesWon,
    }));

    return {
        electionId: rawData.id,
        electionDate: rawData.date,
        electionType: rawData.electionType || 'municipal',
        municipalities,
        summary: {
            totalMunicipalities,
            totalVotes,
            avgTurnout,
            partyTotals,
        },
    };
}

// Helper function to convert basic election data to municipal format
export function convertToMunicipalFormat(basicData: ElectionData, municipalityInfo: any): MunicipalElectionData {
    // Group candidates by party
    const partyMap = new Map<string, { name: string; candidates: any[] }>();
    
    basicData.candidates.forEach(candidate => {
        if (!partyMap.has(candidate.party)) {
            partyMap.set(candidate.party, { name: candidate.party, candidates: [] });
        }
        const result = basicData.results.find(r => r.candidateId === candidate.id);
        partyMap.get(candidate.party)!.candidates.push({
            candidateId: candidate.id,
            candidateName: candidate.name,
            votes: result?.votes || 0,
        });
    });    // Calculate party totals
    const parties = Array.from(partyMap.entries()).map(([partyId, data]) => ({
        partyId,
        partyName: data.name,
        votes: data.candidates.reduce((sum: number, candidate: any) => sum + candidate.votes, 0),
        percentage: 0, // Will be calculated below
        candidates: data.candidates,
    }));

    const totalVotes = parties.reduce((sum: number, party: any) => sum + party.votes, 0);
    parties.forEach((party: any) => {
        party.percentage = totalVotes > 0 ? (party.votes / totalVotes * 100) : 0;
    });

    const winningParty = parties.reduce((max, party) => party.votes > max.votes ? party : max, parties[0]);

    return {
        electionId: basicData.electionId,
        electionDate: basicData.electionDate,
        electionType: 'municipal',
        municipalities: [{
            municipalityId: municipalityInfo.id || 'unknown',
            municipalityName: municipalityInfo.name || 'Unknown Municipality',
            province: municipalityInfo.province || 'Unknown Province',
            region: municipalityInfo.region || 'Unknown Region',
            totalVoters: municipalityInfo.totalVoters || totalVotes,
            totalVotes,
            turnout: municipalityInfo.turnout || 100,
            parties,
        }],
        summary: {
            totalMunicipalities: 1,
            totalVotes,
            avgTurnout: municipalityInfo.turnout || 100,
            partyTotals: parties.map(party => ({
                partyId: party.partyId,
                partyName: party.partyName,
                totalVotes: party.votes,
                percentage: party.percentage,
                municipalitiesWon: party.partyId === winningParty.partyId ? 1 : 0,
            })),
        },
    };
}
