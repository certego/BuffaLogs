import { DateRange } from "react-day-picker";
import { BASE_URL } from "./constants";

export const timestampFormat = "YYYY-MM-DDTHH:mm:ssZ";

export async function getUsersPieChart(dateRange?: DateRange): Promise<any> {
    if (dateRange && dateRange.from && dateRange.to) {
      const start = dateRange.from.toISOString().slice(0, -5) + "Z";
      const end = dateRange.to.toISOString().slice(0, -5)+ "Z";
  
      const url = `${BASE_URL}/users_pie_chart_api?start=${start}&end=${end}`;
      try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error('Failed to fetch users pie chart data');
        }
        const data = await response.json();
        return data;    
      } catch (error) {
        console.error(error);
        throw new Error('Failed to fetch users pie chart data');
      }
    } else {
      throw new Error('Invalid date range');
    }
  }
  
export async function getAlertsLineChart(dateRange?: DateRange): Promise<any> {
    if (dateRange && dateRange.from && dateRange.to) {
      const start = dateRange.from.toISOString().slice(0, -5) + "Z";
      const end = dateRange.to.toISOString().slice(0, -5)+ "Z";
  
      const url = `${BASE_URL}/alerts_line_chart_api?start=${start}&end=${end}`;
      try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error('Failed to fetch users alerts chart data');
        }
        const data = await response.json();
        return data;
      } catch (error) {
        console.error(error);
        throw new Error('Failed to fetch users alerts chart data');
      }
    } else {
      throw new Error('Invalid date range');
    }
  }
  
export async function geWorldMapChart(dateRange?: DateRange): Promise<any> {
    if (dateRange && dateRange.from && dateRange.to) {
      const start = dateRange.from.toISOString().slice(0, -5) + "Z";
      const end = dateRange.to.toISOString().slice(0, -5)+ "Z";
  
      const url = `${BASE_URL}/world_map_chart_api?start=${start}&end=${end}`;
      try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error('Failed to fetch users world chart data');
        }
        const data = await response.json();
        return data;
      } catch (error) {
        console.error(error);
        throw new Error('Failed to fetch users world chart data');
      }
    } else {
      throw new Error('Invalid date range');
    }
  }

  export async function getAlerts(dateRange?: DateRange): Promise<any> {
    if (dateRange && dateRange.from && dateRange.to) {
      const start = dateRange.from.toISOString().slice(0, -5) + "Z";
      const end = dateRange.to.toISOString().slice(0, -5)+ "Z";
  
      const url = `${BASE_URL}/alerts_api?start=${start}&end=${end}`;
      try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error('Failed to fetch alerts');
        }
        const data = await response.json();
        return data;
      } catch (error) {
        console.error(error);
        throw new Error('Failed to fetch alerts');
      }
    } else {
      throw new Error('Invalid date range');
    }
  }
  