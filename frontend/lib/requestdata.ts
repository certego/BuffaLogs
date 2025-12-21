import { DateRange } from "react-day-picker";
import { BASE_URL } from "./constants";

export const timestampFormat = "YYYY-MM-DDTHH:mm:ssZ";

// Common date‐range formatter
function formatDateRange(dateRange?: DateRange) {
    if (dateRange && dateRange.from && dateRange.to) {
        const start = dateRange.from.toISOString().slice(0, -5) + "Z";
        const end   = dateRange.to.toISOString().slice(0, -5)   + "Z";
        return { start, end };
    }
    throw new Error("Invalid date range");
}

// Generic fetch + error handler
async function fetchData(
    endpoint: string,
    errorMessage: string,
    dateRange?: DateRange
): Promise<any> {
    const { start, end } = formatDateRange(dateRange);
    const url = `${BASE_URL}/${endpoint}?start=${start}&end=${end}`;
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(errorMessage);
        return await response.json();
    } catch (err) {
        console.error(err);
        throw new Error(errorMessage);
    }
}

// Each API function now delegates to fetchData
export async function getUsersPieChart(dateRange?: DateRange): Promise<any> {
    return fetchData(
        "api/analytics/chart/users/pie/",
        "Failed to fetch users pie chart data",
        dateRange
    );
}

export async function getAlertsLineChart(dateRange?: DateRange): Promise<any> {
    return fetchData(
        "api/analytics/chart/alerts/line/",
        "Failed to fetch users alerts chart data",
        dateRange
    );
}

export async function getWorldMapChart(dateRange?: DateRange): Promise<any> {
    return fetchData(
        "api/analytics/chart/world-map/",
        "Failed to fetch users world chart data",
        dateRange
    );
}

export async function getAlerts(dateRange?: DateRange): Promise<any> {
    return fetchData(
        "api/alerts/",
        "Failed to fetch alerts",
        dateRange
    );
}
