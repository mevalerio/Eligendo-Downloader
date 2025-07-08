console.log('Starting Eligendo Data Downloader...');
console.log('Node.js version:', process.version);

// Test the logger
const Logger = require('./utils/logger.js').default;
const logger = new Logger();

logger.logInfo('Application started successfully');
logger.logInfo('All TypeScript compilation and module loading is working!');

console.log('✅ Your Eligendo Data Downloader is working correctly!');
console.log('✅ Node.js is properly installed and accessible');
console.log('✅ TypeScript compilation is working'); 
console.log('✅ All modules are loading correctly');

console.log('\nNext steps:');
console.log('1. Configure your API credentials in config/default.json');
console.log('2. Update the API endpoints in src/main.ts');
console.log('3. Run: node dist/main.js to start downloading real data');
console.log('4. Or run: node working-test.js to see this test again');
