class Logger {
    logInfo(message: string): void {
        console.log(`[INFO] ${new Date().toISOString()}: ${message}`);
    }

    logError(message: string): void {
        console.error(`[ERROR] ${new Date().toISOString()}: ${message}`);
    }
}

export default Logger;