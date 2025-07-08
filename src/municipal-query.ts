import { MunicipalQueryService } from './services/municipal-query-service';

// Simple console logger
const log = {
    info: (message: string) => console.log(`[INFO] ${new Date().toISOString()}: ${message}`),
    error: (message: string) => console.log(`[ERROR] ${new Date().toISOString()}: ${message}`),
    success: (message: string) => console.log(`[SUCCESS] ${new Date().toISOString()}: ${message}`)
};

async function queryMunicipalityInteractive() {
    const queryService = new MunicipalQueryService();
    
    // Get command line arguments
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.log('\n🏛️  === ELIGENDO MUNICIPAL QUERY TOOL ===\n');
        console.log('Usage: node dist/municipal-query.js <municipality> [date]');
        console.log('Examples:');
        console.log('  node dist/municipal-query.js "Milano"');
        console.log('  node dist/municipal-query.js "Roma" "2024-06-08"');
        console.log('  node dist/municipal-query.js "Napoli" "2024-06-08"');
        console.log('\nAvailable commands:');
        console.log('  --search <partial-name>  : Search for municipalities');
        console.log('  --dates                  : Show available election dates');
        console.log('  --help                   : Show this help message\n');
        return;
    }

    const command = args[0];
    
    if (command === '--help') {
        console.log('\n🏛️  === ELIGENDO MUNICIPAL QUERY TOOL ===\n');
        console.log('This tool allows you to query Italian municipal election results.');
        console.log('\nCommands:');
        console.log('  <municipality> [date]         : Get results for a specific municipality');
        console.log('  --search <partial-name>       : Search for municipalities matching the name');
        console.log('  --dates                       : Show all available election dates');
        console.log('  --help                        : Show this help message');
        console.log('\nExamples:');
        console.log('  node dist/municipal-query.js "Milano"');
        console.log('  node dist/municipal-query.js "Milano" "2024-06-08"');
        console.log('  node dist/municipal-query.js --search "mil"');
        console.log('  node dist/municipal-query.js --dates\n');
        return;
    }

    if (command === '--dates') {
        log.info('Retrieving available election dates...');
        const dates = await queryService.getAvailableDates();
        console.log('\n📅 Available Election Dates:');
        dates.forEach(date => console.log(`  • ${date}`));
        console.log('');
        return;
    }

    if (command === '--search') {
        const searchTerm = args[1];
        if (!searchTerm) {
            log.error('Please provide a search term. Example: --search "mil"');
            return;
        }
        
        log.info(`Searching for municipalities matching "${searchTerm}"...`);
        const municipalities = await queryService.searchMunicipalities(searchTerm);
        
        console.log(`\n🔍 Municipalities matching "${searchTerm}":`);
        if (municipalities.length === 0) {
            console.log('  No municipalities found.');
        } else {
            municipalities.forEach(muni => console.log(`  • ${muni}`));
        }
        console.log('');
        return;
    }

    // Query specific municipality
    const municipalityName = command;
    const date = args[1] || '2024-06-08'; // Default to demo date

    log.info(`Querying results for ${municipalityName} on ${date}...`);
    
    const result = await queryService.queryMunicipality(municipalityName, date);
    
    if (!result.found) {
        log.error(result.error || 'Municipality not found');
        console.log('\n💡 Try using --search to find available municipalities');
        return;
    }

    const muni = result.municipality!;
    
    // Display results in a beautiful format
    console.log('\n🇮🇹 === RISULTATI ELEZIONI COMUNALI ===');
    console.log(`🏛️  Municipality: ${muni.municipalityName}`);
    console.log(`📍 Location: ${muni.province}, ${muni.region}`);
    console.log(`📅 Election Date: ${muni.electionDate}`);
    console.log(`👥 Total Voters: ${muni.totalVoters.toLocaleString()}`);
    console.log(`🗳️  Total Votes: ${muni.totalVotes.toLocaleString()}`);
    console.log(`📈 Turnout: ${muni.turnout.toFixed(1)}%`);
    
    console.log('\n🎯 PARTY RESULTS:');
    muni.parties.forEach(party => {
        const medal = party.position === 1 ? '🥇' : party.position === 2 ? '🥈' : party.position === 3 ? '🥉' : '  ';
        console.log(`${medal} ${party.position}. ${party.partyName}`);
        console.log(`     🗳️  Votes: ${party.votes.toLocaleString()} (${party.percentage.toFixed(1)}%)`);
        
        if (party.candidates && party.candidates.length > 0) {
            console.log(`     👤 Candidates:`);
            party.candidates.forEach(candidate => {
                console.log(`        • ${candidate.candidateName}: ${candidate.votes.toLocaleString()} votes`);
            });
        }
        console.log('');
    });

    log.success(`Query completed for ${muni.municipalityName}`);
}

// Handle errors gracefully
queryMunicipalityInteractive().catch(error => {
    console.error('\n❌ An error occurred:', error.message);
    process.exit(1);
});
