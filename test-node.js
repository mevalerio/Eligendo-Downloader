console.log('Hello from Node.js');
console.log('Node version:', process.version);
console.log('Current directory:', process.cwd());

// Test file system
const fs = require('fs');
const path = require('path');

const dataPath = path.join(__dirname, 'data', 'municipal-election-data.json');
console.log('Checking for data file:', dataPath);

if (fs.existsSync(dataPath)) {
    console.log('✅ Data file exists');
    const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
    console.log('✅ Data loaded successfully');
    console.log('Available municipalities:');
    data.municipalities.forEach(muni => {
        console.log(`  • ${muni.municipalityName} (${muni.province}, ${muni.region})`);
    });
} else {
    console.log('❌ Data file not found');
}
