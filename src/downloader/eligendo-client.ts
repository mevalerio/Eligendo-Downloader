export class EligendoClient {
    private apiUrl: string;
    private apiKey: string;

    constructor(apiUrl: string, apiKey: string) {
        this.apiUrl = apiUrl;
        this.apiKey = apiKey;
    }

    async authenticate(): Promise<boolean> {
        // Implement authentication logic here
        // For now, we will assume authentication is always successful
        return true;
    }

    async fetchData(endpoint: string): Promise<any> {
        const response = await fetch(`${this.apiUrl}/${endpoint}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Error fetching data: ${response.statusText}`);
        }

        return await response.json();
    }
}

export default EligendoClient;