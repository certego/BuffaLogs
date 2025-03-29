import { useDateContext } from '@/contexts/DateContext';
import { getAlertsLineChart } from '@/lib/requestdata';
import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface DataItem {
  date: string;
  value: number;
  type: string;
}

const Barchart: React.FC = () => {
  const [data, setData] = useState<DataItem[]>([]);
  const { date } = useDateContext();

  useEffect(() => {
    const fetchData = async () => {
      try{
        const formattedData: DataItem[] = [];
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
        console.log(formattedData, "formattedData")
      } catch(e) {
        console.log(e, "error");
      }
    };
    fetchData();
  }, [date]);

  return (
    <ResponsiveContainer width="80%" height={200}>
    <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
      <CartesianGrid stroke="#444" strokeDasharray="3 3" />
      <XAxis dataKey="date" stroke="#5B5C60" />
      <YAxis stroke="#5B5C60" />
      <Tooltip
        contentStyle={{ background: '#333', border: 'none', color: '#FF5533' }}
        cursor={{ fill: 'rgba(255,255,255,0.1)' }}
      />
      <Bar dataKey="value" fill="#5B5C60" label={{ position: 'top', fill: '#FF5533' }} />
    </BarChart>
  </ResponsiveContainer>
  );
};

export default Barchart;