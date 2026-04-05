// app/api/lidar-data/route.ts

import { NextRequest } from "next/server";
import fs from 'fs/promises';
import path from 'path';

// Interface for LiDAR data point
interface LidarPoint {
    r: number;
    theta: number;
    phi: number;
    strength: number;
}

// Function to save data to file
async function saveDataToFile(newPoint: LidarPoint) {
    try {
        // Path to the public file
        const filePath = path.join(process.cwd(), 'public', 'puntos.json');

        // Read existing data
        let existingData: LidarPoint[] = [];
        try {
            const fileContent = await fs.readFile(filePath, 'utf-8');
            existingData = JSON.parse(fileContent);
        } catch (error) {
            // If file doesn't exist or is invalid, start with empty array
            console.log("Creating new data file or resetting invalid data");
        }

        // Add new point to the data
        existingData.push(newPoint);

        // Write updated data back to file
        await fs.writeFile(filePath, JSON.stringify(existingData, null, 4), 'utf-8');

        return true;
    } catch (error) {
        console.error("Error saving data to file:", error);
        return false;
    }
}

export async function POST(request: NextRequest) {
    try {
        const data = await request.json();
        const { r, theta, phi, strength } = data;

        // Create a LiDAR data point
        const lidarPoint: LidarPoint = { r, theta, phi, strength };

        console.log("📡 Datos recibidos del LiDAR:");
        console.log(`Distancia (r): ${r} mm`);
        console.log(`Ángulo horizontal (theta): ${theta}°`);
        console.log(`Ángulo vertical (phi): ${phi}°`);
        console.log(`Fuerza de señal: ${strength}`);

        // Save data to file
        await saveDataToFile(lidarPoint);

        return new Response(JSON.stringify({
            message: "Datos recibidos correctamente",
            point: lidarPoint
        }), {
            status: 200,
            headers: {
                "Content-Type": "application/json",
            },
        });
    } catch (error) {
        console.error("❌ Error al procesar datos:", error);
        return new Response(JSON.stringify({ error: "Error al procesar los datos" }), {
            status: 400,
            headers: {
                "Content-Type": "application/json",
            },
        });
    }
}
