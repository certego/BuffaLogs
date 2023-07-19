import Header from "@/components/Header";
import Piechart from "@/components/PieChart";
import Barchart from "@/components/BarChart";
import React from "react";
import MapChart from "@/components/WorldMap";
import LogsTable from "@/components/LogsTable";

export default function Dashboard() {
  return (
    <>
    <div className="h-screen w-screen">
      <Header/>
      <main className="flex flex-col justify-center mt-10">
        <div id="main-div" className="flex flex-row justify-center ">
          <div id="charts" className="w-[63%] flex flex-col space-y-6 ">
            <div
              id="world-chart"
              className="border rounded-2xl flex flex-col justify-center"
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
                <Barchart />
              </div>
            </div>
          </div>
          <div id="spacing" className="w-[2%]"></div>
          <div id="user-logs" className="w-[30%] border rounded-2xl">
            <h2 className="font-SpaceGrotesk text-2xl mt-5 ml-5">User Logs</h2>
            <div className="px-5 py-5 text-left">
            <LogsTable/>
            </div>
          </div>
        </div>
        <div className="pb-10"></div>
      </main>
    </div>
    </>
  );
}
