import fs from 'fs';
import path from 'path';

const dataDirectory = path.join(__dirname, '../../data');

export const saveToFile = (filename: string, data: any): Promise<void> => {
    return new Promise((resolve, reject) => {
        const filePath = path.join(dataDirectory, filename);
        fs.writeFile(filePath, JSON.stringify(data, null, 2), (err) => {
            if (err) {
                return reject(err);
            }
            resolve();
        });
    });
};

export const readFromFile = (filename: string): Promise<any> => {
    return new Promise((resolve, reject) => {
        const filePath = path.join(dataDirectory, filename);
        fs.readFile(filePath, 'utf8', (err, data) => {
            if (err) {
                return reject(err);
            }
            try {
                const parsedData = JSON.parse(data);
                resolve(parsedData);
            } catch (parseError) {
                reject(parseError);
            }
        });
    });
};