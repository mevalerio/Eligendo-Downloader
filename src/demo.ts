import { parseData } from './downloader/data-parser';
import { saveToFile } from './utils/file-manager';

// Simple console logger
const log = {
    info: (message: string) => console.log(`[INFO] ${new Date().toISOString()}: ${message}`),
    error: (message: string) => console.log(`[ERROR] ${new Date().toISOString()}: ${message}`)
};

// Mock data that simulates API response
const mockApiResponse = {
    id: "election-2024-demo",
    date: "2024-07-08",
    candidates: [
        {
            id: "candidate-1",
            name: "Mario Rossi",
            party: "Partito Democratico"
        },
        {
            id: "candidate-2", 
            name: "Giuseppe Verdi",
            party: "Forza Italia"
        },
        {
            id: "candidate-3",
            name: "Anna Bianchi", 
            party: "Movimento 5 Stelle"
        }
    ],
    results: [
        {
            candidateId: "candidate-1",
            votes: 15420
        },
        {
            candidateId: "candidate-2", 
            votes: 12890
        },
        {
            candidateId: "candidate-3",
            votes: 8734
        }
    ]
};

async function demo() {
    try {
        log.info('Starting demo with mock election data...');
        
        // Parse the mock data
        const structuredData = parseData(mockApiResponse);
        log.info('Successfully parsed election data');
        
        // Save to file
        await saveToFile('demo-election-data.json', structuredData);
        log.info('Demo data saved to demo-election-data.json');
        
        // Display some results
        console.log('\n=== DEMO ELECTION RESULTS ===');
        console.log(`Election ID: ${structuredData.electionId}`);
        console.log(`Election Date: ${structuredData.electionDate}`);
        console.log('\nCandidates:');
        structuredData.candidates.forEach(candidate => {
            const result = structuredData.results.find(r => r.candidateId === candidate.id);
            const votes = result ? result.votes : 0;
            console.log(`- ${candidate.name} (${candidate.party}): ${votes} votes`);
        });
        
        const totalVotes = structuredData.results.reduce((sum, result) => sum + result.votes, 0);
        console.log(`\nTotal votes: ${totalVotes}`);
        
        log.info('Demo completed successfully!');
        
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        log.error('Demo failed: ' + errorMessage);
    }
}

demo();
