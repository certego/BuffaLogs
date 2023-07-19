import React, { useEffect, useState, useMemo } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker
} from "react-simple-maps";
import { csv } from "d3-fetch";
import { scaleLinear } from "d3-scale";
import sortBy from "lodash/sortBy";


interface City {
  population: number;
  city_code: string;
  city: string;
  lat: number;
  lng: number;
}

const geoUrl =
  "https://raw.githubusercontent.com/deldersveld/topojson/master/world-continents.json";

const MapChart = () => {
  const [data, setData] = useState<City[]>([]);
  const [maxValue, setMaxValue] = useState<Number>(0);

  useEffect(() => {
    csv("/data.csv").then((cities: any) => {
      const sortedCities = sortBy(cities, (o: any) => -o.population);
      setMaxValue(sortedCities[0].population);
      setData(sortedCities);
    });
  }, []);

  const popScale = useMemo(
    () => scaleLinear().domain([0, maxValue]).range([0, 24]),
    [maxValue]
  );

  return (
    <div className="">
    <ComposableMap projectionConfig={{ rotate: [-10, 0, 0] }}>
      <Geographies geography={geoUrl}>
        {({ geographies }) =>
          geographies.map((geo) => (
            <Geography key={geo.rsmKey} geography={geo} fill="#5B5C60" />
          ))
        }
      </Geographies>
      {data.map(({ city_code, lng, lat, population }) => {
        return (
          <Marker key={city_code} coordinates={[lng, lat]}>
            <circle fill="#F53" stroke="#FFF" r={popScale(population)} />
          </Marker>
        );
      })}
    </ComposableMap>
    </div>
  );
};

export default MapChart;
