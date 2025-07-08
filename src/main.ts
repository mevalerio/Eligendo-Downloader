import { EligendoClient } from './downloader/eligendo-client';
import { parseData } from './downloader/data-parser';
import Logger from './utils/logger';
import { saveToFile } from './utils/file-manager';

const logger = new Logger();
const client = new EligendoClient('https://api.eligendo.it/elections', 'your-api-key');

async function main() {
    try {
        logger.logInfo('Starting the data download process...');
        
        await client.authenticate();
        const rawData = await client.fetchData('results');
        const structuredData = parseData(rawData);
        
        await saveToFile('election-data.json', structuredData);
        logger.logInfo('Data downloaded and saved successfully.');
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        logger.logError('An error occurred during the data download process: ' + errorMessage);
    }
}

main();