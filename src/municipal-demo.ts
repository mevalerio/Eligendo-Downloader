import { parseMunicipalData } from './downloader/municipal-data-parser';
import { saveToFile } from './utils/file-manager';

// Simple console logger
const log = {
    info: (message: string) => console.log(`[INFO] ${new Date().toISOString()}: ${message}`),
    error: (message: string) => console.log(`[ERROR] ${new Date().toISOString()}: ${message}`)
};

// Mock data for Italian municipal elections with multiple municipalities
const mockMunicipalData = {
    id: "elezioni-comunali-2024",
    date: "2024-06-08",
    electionType: "municipal",
    municipalities: [
        {
            id: "milano",
            name: "Milano",
            province: "Milano",
            region: "Lombardia",
            totalVoters: 850000,
            totalVotes: 680000,
            turnout: 80.0,
            parties: [
                {
                    id: "pd",
                    name: "Partito Democratico",
                    votes: 272000,
                    percentage: 40.0,
                    candidates: [
                        { id: "rossi-milano", name: "Giuseppe Sala", votes: 272000 }
                    ]
                },
                {
                    id: "lega",
                    name: "Lega",
                    votes: 204000,
                    percentage: 30.0,
                    candidates: [
                        { id: "verdi-milano", name: "Luca Bernardo", votes: 204000 }
                    ]
                },
                {
                    id: "m5s",
                    name: "Movimento 5 Stelle",
                    votes: 136000,
                    percentage: 20.0,
                    candidates: [
                        { id: "bianchi-milano", name: "Layla Pavone", votes: 136000 }
                    ]
                },
                {
                    id: "fi",
                    name: "Forza Italia",
                    votes: 68000,
                    percentage: 10.0,
                    candidates: [
                        { id: "neri-milano", name: "Alessandro Moratti", votes: 68000 }
                    ]
                }
            ]
        },
        {
            id: "roma",
            name: "Roma",
            province: "Roma",
            region: "Lazio",
            totalVoters: 1200000,
            totalVotes: 900000,
            turnout: 75.0,
            parties: [
                {
                    id: "pd",
                    name: "Partito Democratico",
                    votes: 450000,
                    percentage: 50.0,
                    candidates: [
                        { id: "rossi-roma", name: "Roberto Gualtieri", votes: 450000 }
                    ]
                },
                {
                    id: "lega",
                    name: "Lega",
                    votes: 180000,
                    percentage: 20.0,
                    candidates: [
                        { id: "verdi-roma", name: "Enrico Michetti", votes: 180000 }
                    ]
                },
                {
                    id: "m5s",
                    name: "Movimento 5 Stelle",
                    votes: 180000,
                    percentage: 20.0,
                    candidates: [
                        { id: "bianchi-roma", name: "Virginia Raggi", votes: 180000 }
                    ]
                },
                {
                    id: "fi",
                    name: "Forza Italia",
                    votes: 90000,
                    percentage: 10.0,
                    candidates: [
                        { id: "neri-roma", name: "Carlo Calenda", votes: 90000 }
                    ]
                }
            ]
        },
        {
            id: "napoli",
            name: "Napoli",
            province: "Napoli",
            region: "Campania",
            totalVoters: 650000,
            totalVotes: 455000,
            turnout: 70.0,
            parties: [
                {
                    id: "m5s",
                    name: "Movimento 5 Stelle",
                    votes: 227500,
                    percentage: 50.0,
                    candidates: [
                        { id: "bianchi-napoli", name: "Gaetano Manfredi", votes: 227500 }
                    ]
                },
                {
                    id: "pd",
                    name: "Partito Democratico",
                    votes: 136500,
                    percentage: 30.0,
                    candidates: [
                        { id: "rossi-napoli", name: "Antonio Bassolino", votes: 136500 }
                    ]
                },
                {
                    id: "lega",
                    name: "Lega",
                    votes: 68250,
                    percentage: 15.0,
                    candidates: [
                        { id: "verdi-napoli", name: "Catello Maresca", votes: 68250 }
                    ]
                },
                {
                    id: "fi",
                    name: "Forza Italia",
                    votes: 22750,
                    percentage: 5.0,
                    candidates: [
                        { id: "neri-napoli", name: "Matteo Brambilla", votes: 22750 }
                    ]
                }
            ]
        }
    ]
};

async function municipalDemo() {
    try {
        log.info('Starting municipal election demo with Italian cities...');
        
        // Parse the municipal data
        const structuredData = parseMunicipalData(mockMunicipalData);
        log.info('Successfully parsed municipal election data');
        
        // Save to file
        await saveToFile('municipal-election-data.json', structuredData);
        log.info('Municipal data saved to municipal-election-data.json');
        
        // Display detailed results
        console.log('\n🇮🇹 === ELEZIONI COMUNALI ITALIANE 2024 ===');
        console.log(`📊 Election ID: ${structuredData.electionId}`);
        console.log(`📅 Election Date: ${structuredData.electionDate}`);
        console.log(`🏛️  Election Type: ${structuredData.electionType}`);
        
        console.log(`\n📍 MUNICIPALITIES (${structuredData.summary.totalMunicipalities}):`);
        
        structuredData.municipalities.forEach(municipality => {
            console.log(`\n🏙️  ${municipality.municipalityName} (${municipality.province}, ${municipality.region})`);
            console.log(`   👥 Total Voters: ${municipality.totalVoters.toLocaleString()}`);
            console.log(`   🗳️  Total Votes: ${municipality.totalVotes.toLocaleString()}`);
            console.log(`   📈 Turnout: ${municipality.turnout.toFixed(1)}%`);
            console.log(`   🎯 Party Results:`);
            
            municipality.parties
                .sort((a, b) => b.votes - a.votes)
                .forEach((party, index) => {
                    const position = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '  ';
                    console.log(`     ${position} ${party.partyName}: ${party.votes.toLocaleString()} votes (${party.percentage.toFixed(1)}%)`);
                    if (party.candidates && party.candidates.length > 0) {
                        console.log(`        👤 ${party.candidates[0].candidateName}`);
                    }
                });
        });
        
        console.log(`\n📊 NATIONAL SUMMARY:`);
        console.log(`🏛️  Total Municipalities: ${structuredData.summary.totalMunicipalities}`);
        console.log(`🗳️  Total Votes Cast: ${structuredData.summary.totalVotes.toLocaleString()}`);
        console.log(`📈 Average Turnout: ${structuredData.summary.avgTurnout.toFixed(1)}%`);
        
        console.log(`\n🎯 PARTY PERFORMANCE ACROSS ALL MUNICIPALITIES:`);
        structuredData.summary.partyTotals
            .sort((a, b) => b.totalVotes - a.totalVotes)
            .forEach((party, index) => {
                const position = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '  ';
                console.log(`${position} ${party.partyName}:`);
                console.log(`   🗳️  Total Votes: ${party.totalVotes.toLocaleString()} (${party.percentage.toFixed(1)}%)`);
                console.log(`   🏆 Municipalities Won: ${party.municipalitiesWon}/${structuredData.summary.totalMunicipalities}`);
            });
        
        log.info('Municipal election demo completed successfully!');
        
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        log.error('Municipal demo failed: ' + errorMessage);
    }
}

municipalDemo();
