console.log('Testing Node.js installation...');
console.log('Node.js version:', process.version);
console.log('Current directory:', process.cwd());

// Check if we can access file system
const fs = require('fs');
const path = require('path');

try {
    // List files in current directory
    const files = fs.readdirSync('.');
    console.log('Files in current directory:', files);
} catch (error) {
    console.log('Error reading directory:', error.message);
}

// Simple mock data test
const mockData = {
    election: 'Test Election 2024',
    date: '2024-07-08',
    results: [
        { candidate: 'Candidate A', party: 'Party 1', votes: 1000, percentage: 55.6 },
        { candidate: 'Candidate B', party: 'Party 2', votes: 800, percentage: 44.4 }
    ]
};

console.log('\nMock election data:');
console.log(JSON.stringify(mockData, null, 2));

// Test JSON file creation
try {
    fs.writeFileSync('test-output.json', JSON.stringify(mockData, null, 2));
    console.log('\nSuccessfully created test-output.json');
} catch (error) {
    console.log('Error creating file:', error.message);
}

console.log('\nTest completed successfully!');
console.log('If you see this message, Node.js is working properly.');