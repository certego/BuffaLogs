import { useDateContext } from "@/contexts/DateContext";
import { getUsersPieChart } from "@/lib/requestdata";
import dynamic from "next/dynamic";
import React, { useEffect, useState } from "react";
import {
  Pie,
  Cell,
  Label,
  Sector,
} from "recharts";
const PieChart = dynamic(
  () => import("recharts").then((recharts) => recharts.PieChart),
  { ssr: false }
);

const RADIAN = Math.PI / 180;
const cx = 170;
const cy = 200;
const iR = 50;
const oR = 100;
const value = 50;

const Piechart: React.FC = () => {
  interface pieDataType {
    type: string;
    value: number;
    color: string;
  }
  const [label, setLabel] = useState("Risk Levels");
  const [activeIndex, setActiveIndex] = useState<number | number[]>(0);
  const [data, setData] = useState<pieDataType[]>([]);
  const { date } = useDateContext();

  const onPieEnter = (_: any, index: number) => {
    setActiveIndex(index);
  };

  useEffect(() => {
    const colors = ["#5B5C60", "#5e4C60", "#5B5C60", "#FF5533"];
    const fetchData = async () => {
      try {
        const updateData = await getUsersPieChart(date);
        const formattedData = Object.keys(updateData).map((type, index) => ({
          type,
          value: updateData[type],
          color: colors[index % colors.length],
        }));
        setData(formattedData);
      } catch (e) {}
    };
    fetchData();
  }, [date]);

  interface ActiveShapeProps {
    cx: number;
    cy: number;
    midAngle: number;
    innerRadius: number;
    outerRadius: number;
    startAngle: number;
    endAngle: number;
    fill: any;
    value: number;
    payload: any;
  }
  
  const renderActiveShape = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    startAngle,
    endAngle,
    fill,
    value,
    payload,
  }: ActiveShapeProps) => {
    const RADIAN = Math.PI / 180;

    const sin = Math.sin(-RADIAN * midAngle);
    const cos = Math.cos(-RADIAN * midAngle);
    const sx = cx + (outerRadius + 10) * cos;
    const sy = cy + (outerRadius + 10) * sin;
    const mx = cx + (outerRadius + 30) * cos;
    const my = cy + (outerRadius + 30) * sin;
    const ex = mx + (cos >= 0 ? 1 : -1) * 22;
    const ey = my;
    const textAnchor = cos >= 0 ? "start" : "end";

    return (
      <g>
        <Sector
          cx={cx}
          cy={cy}
          innerRadius={innerRadius}
          outerRadius={outerRadius}
          startAngle={startAngle}
          endAngle={endAngle}
          fill={fill}
        />
        <Sector
          cx={cx}
          cy={cy}
          startAngle={startAngle}
          endAngle={endAngle}
          innerRadius={outerRadius + 6}
          outerRadius={outerRadius + 10}
          fill={fill}
        />
        <path
          d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`}
          stroke={fill}
          fill="none"
        />
        <circle cx={ex} cy={ey} r={2} fill={fill} stroke="none" />
        <text
          x={ex + (cos >= 0 ? 1 : -1) * 12}
          y={ey}
          textAnchor={textAnchor}
          fill="#fff"
        >{`${payload.type} ${value}`}</text>
      </g>
    );
  };

  return (
    <PieChart width={400} height={250}>
      <Pie
        activeIndex={activeIndex}
        activeShape={renderActiveShape}
        dataKey="value"
        startAngle={0}
        endAngle={180}
        data={data}
        cx={cx}
        cy={cy}
        innerRadius={iR}
        outerRadius={oR}
        fill="#8884d8"
        stroke="none"
        onMouseEnter={onPieEnter}
      >
        {data.map((entry, index) => (
          <Cell key={`cell-${index}`} fill={entry.color}></Cell>
        ))}
        <Label value={label} color="fff" position="center" />
      </Pie>
    </PieChart>
  );
};

export default Piechart;
