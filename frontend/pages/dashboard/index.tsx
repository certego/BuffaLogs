import React, { useState } from "react";
import Header from "@/components/Header";
import Piechart from "@/components/PieChart";
import Barchart from "@/components/BarChart";
import LogsTable from "@/components/LogsTable";
import MapChart from "@/components/Worldmap";
import { AlertsFilter } from "@/components/AlertsFilter";

// Define the type for an alert
interface Alert {
  id: string;
  type: string;
  severity: string;
  timestamp: string;
  location: string;
  details: string;
}

// Define the type for filters
interface AlertFilters {
  keyword?: string;
  alertType?: string;
  severity?: string;
  dateRange?: {
    from?: Date;
    to?: Date;
  };
  location?: string;
}

export default function Dashboard() {
  // Mock data - in a real application, this would come from an API
  const [alerts, setAlerts] = useState<Alert[]>([
    {
      id: "1",
      type: "impossible_travel",
      severity: "high",
      timestamp: "2025-03-28T10:30:00Z",
      location: "us",
      details: "Suspicious login from multiple locations"
    },
    {
      id: "2",
      type: "new_device",
      severity: "medium",
      timestamp: "2025-03-28T11:45:00Z",
      location: "eu",
      details: "New device detected for user account"
    },
    // Add more mock alerts as needed
  ]);

  const [filteredAlerts, setFilteredAlerts] = useState<Alert[]>(alerts);

  const handleApplyFilters = (filters: AlertFilters) => {
    const filtered = alerts.filter(alert => {
      // Keyword filter
      const keywordMatch = !filters.keyword || 
        alert.details.toLowerCase().includes(filters.keyword.toLowerCase());
  
      // Alert Type filter
      const typeMatch = !filters.alertType || 
        alert.type === filters.alertType;
  
      // Severity filter
      const severityMatch = !filters.severity || 
        alert.severity === filters.severity;
  
      // Date Range filter
      const dateMatch = (!filters.dateRange?.from || new Date(alert.timestamp) >= filters.dateRange.from) &&
        (!filters.dateRange?.to || new Date(alert.timestamp) <= filters.dateRange.to);
  
      // Location filter
      const locationMatch = !filters.location || 
        alert.location.toLowerCase() === filters.location.toLowerCase();
  
      return keywordMatch && typeMatch && severityMatch && dateMatch && locationMatch;
    });
  
    setFilteredAlerts(filtered);
  };

  return (
    <>
    <div className="h-screen w-screen">
      <Header/>
      <main className="flex flex-col justify-center mt-10">
        {/* Alerts Filter Section */}
        <div className="px-10 mb-6">
          <AlertsFilter onApplyFilters={handleApplyFilters} />
        </div>

        <div id="main-div" className="flex flex-row justify-center ">
          <div id="charts" className="w-[63%] flex flex-col space-y-6 ">
            <div
              id="world-chart"
              className="border rounded-2xl flex flex-col justify-center "
            >
              <h2 className="font-SpaceGrotesk text-2xl mt-5 ml-5">
                Login Locations
              </h2>
              <div className="max-w-xl xl:max-w-2xl">
                <MapChart />
              </div>
            </div>
            <div
              id="misc-graphs"
              className="flex flex-row justify-evenly items-center space-x-4 w-full"
            >
              <div className="border rounded-2xl w-1/2">
                <h2 className="font-SpaceGrotesk text-2xl mt-5 ml-5">
                  Risk Chart
                </h2>
                <Piechart />
              </div>

              <div className="border rounded-2xl h-full w-full flex flex-col justify-between ">
                <h2 className="font-SpaceGrotesk text-2xl mt-5 ml-5">
                  Login Alerts
                </h2>
                <Barchart/>
              </div>
            </div>
          </div>
          <div id="spacing" className="w-[2%]"></div>
          <div id="user-logs" className="w-[30%] border rounded-2xl">
            <h2 className="font-SpaceGrotesk text-2xl mt-5 ml-5">User Alerts</h2>
            <div className="px-5 py-5 text-left">
              {/* Filtered Alerts Table */}
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border p-2">Type</th>
                      <th className="border p-2">Severity</th>
                      <th className="border p-2">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAlerts.map(alert => (
                      <tr key={alert.id} className="hover:bg-gray-50">
                        <td className="border p-2">{alert.type}</td>
                        <td className="border p-2">{alert.severity}</td>
                        <td className="border p-2">{alert.details}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredAlerts.length === 0 && (
                  <div className="text-center py-4">No alerts found</div>
                )}
              </div>
            </div>
          </div>
        </div>
        <div className="pb-10"></div>
      </main>
    </div>
    </>
  );
}