import { EligendoMunicipalAPI, quickQuery, quickWinner } from './eligendo-api';

// Simple console logger
const log = {
    info: (message: string) => console.log(`[INFO] ${new Date().toISOString()}: ${message}`),
    error: (message: string) => console.log(`[ERROR] ${new Date().toISOString()}: ${message}`),
    success: (message: string) => console.log(`[SUCCESS] ${new Date().toISOString()}: ${message}`)
};

async function demonstrateQueryAPI() {
    console.log('\n🏛️  === ELIGENDO MUNICIPAL QUERY API DEMO ===\n');
    
    const api = new EligendoMunicipalAPI();
    
    try {
        // Example 1: Query specific municipality
        log.info('Example 1: Querying Milano results...');
        const milanResult = await api.getMunicipalityResults('Milano', '2024-06-08');
        
        if (milanResult.found && milanResult.municipality) {
            console.log(`\n📊 ${milanResult.municipality.municipalityName} Election Results:`);
            console.log(`📍 Location: ${milanResult.municipality.province}, ${milanResult.municipality.region}`);
            console.log(`📈 Turnout: ${milanResult.municipality.turnout.toFixed(1)}%`);
            console.log(`🎯 Party Results:`);
            
            milanResult.municipality.parties.forEach(party => {
                const medal = party.position === 1 ? '🥇' : party.position === 2 ? '🥈' : party.position === 3 ? '🥉' : '  ';
                console.log(`   ${medal} ${party.partyName}: ${party.votes.toLocaleString()} votes (${party.percentage.toFixed(1)}%)`);
            });
        } else {
            console.log(`❌ ${milanResult.error}`);
        }

        // Example 2: Search for municipalities
        log.info('\nExample 2: Searching for municipalities containing "mil"...');
        const searchResults = await api.searchMunicipalities('mil');
        console.log(`🔍 Found ${searchResults.length} municipalities:`);
        searchResults.forEach(muni => console.log(`   • ${muni}`));

        // Example 3: Get simplified party results
        log.info('\nExample 3: Getting simplified party results for Roma...');
        const romaParties = await api.getPartyResults('Roma');
        
        if (romaParties) {
            console.log(`\n🏛️  ${romaParties.municipalityName} - Simple Party Results:`);
            romaParties.parties.forEach(party => {
                console.log(`   ${party.position}. ${party.name}: ${party.votes.toLocaleString()} votes (${party.percentage.toFixed(1)}%)`);
            });
        }

        // Example 4: Get winning party
        log.info('\nExample 4: Getting winning party for each city...');
        const cities = ['Milano', 'Roma', 'Napoli'];
        
        for (const city of cities) {
            const winner = await api.getWinningParty(city);
            if (winner) {
                console.log(`🏆 ${winner.municipalityName}: ${winner.winningParty} won with ${winner.votes.toLocaleString()} votes (${winner.percentage.toFixed(1)}%)`);
                if (winner.margin) {
                    console.log(`   Margin: ${winner.margin.toLocaleString()} votes`);
                }
            }
        }

        // Example 5: Quick query functions
        log.info('\nExample 5: Using quick query functions...');
        await quickQuery('Napoli');
        await quickWinner('Milano');

        // Example 6: Available dates
        log.info('\nExample 6: Getting available election dates...');
        const dates = await api.getAvailableDates();
        console.log(`📅 Available dates: ${dates.join(', ')}`);

        // Example 7: Error handling
        log.info('\nExample 7: Error handling with non-existent municipality...');
        const invalidResult = await api.getMunicipalityResults('NonExistentCity');
        console.log(`❌ ${invalidResult.error}`);

        log.success('All query examples completed successfully!');
        
    } catch (error) {
        log.error(`Demo failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

// Usage examples as standalone functions
async function exampleUsage() {
    console.log('\n📖 === USAGE EXAMPLES ===\n');
    
    const api = new EligendoMunicipalAPI();
    
    // Simple usage: Get results for Milano
    console.log('// Get results for Milano');
    console.log('const result = await api.getMunicipalityResults("Milano", "2024-06-08");');
    
    const result = await api.getMunicipalityResults('Milano', '2024-06-08');
    if (result.found) {
        console.log('// Result found!');
        console.log(`console.log("${result.municipality!.municipalityName} winner: ${result.municipality!.parties[0].partyName}");`);
    }
    
    console.log('\n// Search for municipalities');
    console.log('const cities = await api.searchMunicipalities("mil");');
    const cities = await api.searchMunicipalities('mil');
    console.log(`// Found: ${cities.join(', ')}`);
    
    console.log('\n// Get winning party');
    console.log('const winner = await api.getWinningParty("Roma");');
    const winner = await api.getWinningParty('Roma');
    if (winner) {
        console.log(`// Winner: ${winner.winningParty} with ${winner.votes.toLocaleString()} votes`);
    }
}

// Run the demo
demonstrateQueryAPI().then(() => {
    return exampleUsage();
}).catch(error => {
    console.error('❌ Demo failed:', error.message);
    process.exit(1);
});
