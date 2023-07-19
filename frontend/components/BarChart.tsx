import { useDateContext } from "@/contexts/DateContext";
import { getAlertsLineChart } from "@/lib/requestdata";
import { get } from "lodash";
import React, { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const Barchart: React.FC = () => {
  interface alertDataType {
      date: string,
      value: number,
      type: string,
  }

  const [data, setData] = useState<alertDataType[]>([]);
  const { date } = useDateContext();

  useEffect(() => {
    const fetchData = async () => {
      try{
        const formattedData: alertDataType[] = [];
        const updateData = await getAlertsLineChart(date);
        for (const key in updateData) {
          if (key !== 'Timeframe') {
            const date = key;
            const value = updateData[key];
            const type = updateData['Timeframe'];
      
            const newDataItem = {
              date: date,
              value: value,
              type: type,
            };
      
            formattedData.push(newDataItem);
          }
        }
        setData(formattedData);
      } catch(e) {
        console.log(e, "error");
      }
    };
    fetchData();
  }, [date]);

  const [activeIndex, setActiveIndex] = useState(0);
  const activeItem = data[activeIndex];

  const handleClick = (data: any, index: number) => {
    setActiveIndex(index);
  };

  return (
    <div style={{ width: "80%" }} className="mx-10 my-10 ">
      <ResponsiveContainer width="100%" height={100}>
        <BarChart width={150} height={40} data={data}>
          <Bar dataKey="value" onClick={handleClick}>
            {data.map((entry, index) => (
              <Cell
                cursor="pointer"
                fill={index === activeIndex ? "#FF5533" : "#5B5C60"}
                key={`cell-${index}`}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="content font-SpaceGrotesk">{`Alerts on ${activeItem?.date}`}</p>
    </div>
  );
};

export default Barchart;
