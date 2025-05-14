'use server'

import fs from 'fs/promises'
import path from 'path'

/**
 * Server action to delete all LiDAR data from the storage file
 */
export async function clearLidarData() {
    try {
        // Clear the public file
        const filePath = path.join(process.cwd(), 'public', 'puntos.json')
        await fs.writeFile(filePath, '[]', 'utf-8')

        return { success: true, message: 'LiDAR data cleared successfully' }
    } catch (error) {
        console.error('Error clearing LiDAR data:', error)
        return { success: false, message: 'Failed to clear LiDAR data' }
    }
}
