import React, { useEffect, useState, useMemo } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  ZoomableGroup
} from "react-simple-maps";
import { csv } from "d3-fetch";
import { scaleLinear } from "d3-scale";
import sortBy from "lodash/sortBy";
import { getWorldMapChart } from "@/lib/requestdata";
import { useDateContext } from "@/contexts/DateContext";


interface Country {
  country: string;
  lat: number;
  lon: number;
  alerts: number;
}

const geoUrl =
  "https://raw.githubusercontent.com/deldersveld/topojson/master/world-continents.json";

const MapChart = () => {
  const [data, setData] = useState<Country[]>([]);
  const [maxValue, setMaxValue] = useState<Number>(0);
  const {date} = useDateContext();

  useEffect(() => {
    const fetchData = async () => {
      const data = await getWorldMapChart(date)
      setData(data);
    }
  fetchData();
  }, [date]);

  const popScale = useMemo(
    () => scaleLinear().domain([0, maxValue]).range([0, 24]),
    [maxValue]
  );

  return (
    <div className="">
    <ComposableMap projectionConfig={{ rotate: [-10, 0, 0] }}>
    <ZoomableGroup center={[0, 0]} zoom={1}>
      <Geographies geography={geoUrl}>
        {({ geographies }) =>
          geographies.map((geo) => (
            <Geography key={geo.rsmKey} geography={geo} fill="#5B5C60" />
          ))
        }
      </Geographies>
      {data.map(({ country, lat, lon, alerts }) => {
        return (
          <Marker key={country} coordinates={[lon, lat]}>
            <circle fill="#F53" stroke="#FFF" r={popScale(alerts)} />
          </Marker>
        );
      })}
       </ZoomableGroup>
    </ComposableMap>
    </div>
  );
};

export default MapChart;
