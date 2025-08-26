import React, { useEffect, useState, useMemo } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  ZoomableGroup,
} from "react-simple-maps";
import { scaleLinear } from "d3-scale";
import { getWorldMapChart } from "@/lib/requestdata";
import { useDateContext } from "@/contexts/DateContext";

interface Country {
  country: string;
  lat: number;
  lon: number;
  alerts: number;
}

const geoUrl =
  "https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson";

const MapChart = () => {
  const [data, setData] = useState<Country[]>([]);
  const [zoom, setZoom] = useState<number>(1);
  const [maxValue, setMaxValue] = useState<number>(0);
  const { date } = useDateContext();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result: Country[] = await getWorldMapChart(date);
        setData(result);
        
        if (result.length > 0) {
          const maxAlerts = Math.max(...result.map(country => country.alerts));
          setMaxValue(maxAlerts);
        } else {
          setMaxValue(0);
        }
      } catch (err) {
        setData([]);
        setMaxValue(0);
      }
    };
    
    if (date) {
      fetchData();
    } else {
      setData([]);
      setMaxValue(0);
    }
  }, [date]);

  const popScale = useMemo(
    () => scaleLinear().domain([0, maxValue]).range([0, 12]),
    [maxValue]
  );

  return (
    <div className="w-full h-96">
      <ComposableMap
        projectionConfig={{
          rotate: [-10, 0, 0],
          scale: 147
        }}
        width={800}
        height={384}
        style={{ width: "100%", height: "100%" }}
      >
        <ZoomableGroup
          center={[0, 0]}
          zoom={zoom}
          maxZoom={6}
          onMoveEnd={({ coordinates, zoom }) => {
            setZoom(zoom);
          }}
        >
          <Geographies geography={geoUrl}>
            {({ geographies }) =>
              geographies.map((geo) => (
                <Geography 
                  key={geo.rsmKey} 
                  geography={geo} 
                  fill="#5B5C60" 
                  stroke="#FFFFFF"
                  strokeWidth={0.5}
                />
              ))
            }
          </Geographies>
          {data.map(({ country, lat, lon, alerts }) => (
            <Marker key={country} coordinates={[lon, lat]}>
              <circle
                fill="#F53"
                stroke="#FFF"
                strokeWidth={2}
                r={Math.max(2, popScale(alerts) / zoom)}
              />
            </Marker>
          ))}
        </ZoomableGroup>
      </ComposableMap>
    </div>
  );
};

export default MapChart;
