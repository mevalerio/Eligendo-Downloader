// Simple test of the query functionality
console.log('Starting municipal query test...');

const fs = require('fs');
const path = require('path');

// Read the municipal election data
const dataPath = path.join(__dirname, 'data', 'municipal-election-data.json');

console.log('Reading data from:', dataPath);

if (fs.existsSync(dataPath)) {
    const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
    console.log('Data loaded successfully');
    
    // Function to query municipality
    function queryMunicipality(municipalityName, date = '2024-06-08') {
        console.log(`\nQuerying: ${municipalityName} on ${date}`);
        
        const municipality = data.municipalities.find(muni => 
            muni.municipalityName.toLowerCase() === municipalityName.toLowerCase() ||
            muni.municipalityName.toLowerCase().includes(municipalityName.toLowerCase())
        );
        
        if (!municipality) {
            console.log(`❌ Municipality "${municipalityName}" not found`);
            console.log('Available municipalities:');
            data.municipalities.forEach(muni => {
                console.log(`  • ${muni.municipalityName} (${muni.province}, ${muni.region})`);
            });
            return null;
        }
        
        console.log(`\n🏛️  === ${municipality.municipalityName.toUpperCase()} ELECTION RESULTS ===`);
        console.log(`📍 Location: ${municipality.province}, ${municipality.region}`);
        console.log(`📅 Date: ${data.electionDate}`);
        console.log(`👥 Total Voters: ${municipality.totalVoters.toLocaleString()}`);
        console.log(`🗳️  Total Votes: ${municipality.totalVotes.toLocaleString()}`);
        console.log(`📈 Turnout: ${municipality.turnout.toFixed(1)}%`);
        
        console.log('\n🎯 PARTY RESULTS:');
        const sortedParties = municipality.parties.sort((a, b) => b.votes - a.votes);
        
        sortedParties.forEach((party, index) => {
            const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '  ';
            console.log(`${medal} ${index + 1}. ${party.partyName}`);
            console.log(`     🗳️  Votes: ${party.votes.toLocaleString()} (${party.percentage.toFixed(1)}%)`);
            
            if (party.candidates && party.candidates.length > 0) {
                console.log(`     👤 Candidates:`);
                party.candidates.forEach(candidate => {
                    console.log(`        • ${candidate.candidateName}: ${candidate.votes.toLocaleString()} votes`);
                });
            }
        });
        
        return municipality;
    }
    
    // Get command line arguments
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.log('\n📖 Usage: node simple-query.js <municipality> [date]');
        console.log('Examples:');
        console.log('  node simple-query.js Milano');
        console.log('  node simple-query.js Roma');
        console.log('  node simple-query.js Napoli');
        console.log('');
        
        // Show available municipalities
        console.log('📍 Available municipalities:');
        data.municipalities.forEach(muni => {
            console.log(`  • ${muni.municipalityName} (${muni.province}, ${muni.region})`);
        });
        console.log('');
        
    } else {
        const municipalityName = args[0];
        const date = args[1] || '2024-06-08';
        
        queryMunicipality(municipalityName, date);
    }
    
} else {
    console.log('❌ Municipal election data file not found at:', dataPath);
    console.log('Please run the municipal demo first: node dist/municipal-demo.js');
}
