import Header from "@/components/Header";
import BarChart from "@/components/BarChart";
import Piechart from "@/components/PieChart";
import MapChart from "@/components/Worldmap";

export const data = [
  ["Task", "Hours per Day"],
  ["high", 7],
  ["low", 7],
];

export const options = {
  title: "user risk level",
  backgroundColor: "#030712",
  titleTextStyle: "#000000",
  colors: ["#131313", "#101010"],
};

export default function Dashboard() {
  //width se manuover horha hai
  return (
    <>
      <Header />
      <main className="w-screen flex flex-col justify-center mt-10">
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
              className="flex flex-row justify-items-stretch items-center space-x-4 w-full"
            >
              <div id="pie-charts" className="border rounded-2xl w-1/2">
              <h2 className="font-SpaceGrotesk text-2xl mt-5 ml-5">
                PieChart
              </h2>
                <Piechart/>
              </div>
              <div id="bar-chart" className="border rounded-2xl">
                {/* <PieChart/> */}
              </div>
            </div>
          </div>
          <div id="spacing" className="w-[2%]"></div>
          <div id="user-logs" className="w-[30%] border rounded-2xl">
            <h2 className="font-SpaceGrotesk text-2xl mt-5 ml-5">User Logs</h2>
          </div>
          
        </div>
        <div className="pb-10"></div>
      </main>
    </>
  );
}
