import { addDays } from "date-fns";
import React, { createContext, useContext, useState } from "react";
import { DateRange } from "react-day-picker";

interface DateContextState {
  date: DateRange | undefined;
  setDate: React.Dispatch<React.SetStateAction<DateRange | undefined>>;
}

const DateContext = createContext<DateContextState | null>(null);

interface DateContextProviderProps {
  children: React.ReactNode;
}

export const DateContextProvider: React.FC<DateContextProviderProps> = ({ children }) => {
  const [date, setDate] = useState<DateRange | undefined>(() => {
    const today = new Date();
    return {
      from: addDays(today, -7),
      to: today,
    };
  });

  return (
    <DateContext.Provider value={{ date, setDate }}>
      {children}
    </DateContext.Provider>
  );
};


export const useDateContext = () => {
  const context = useContext(DateContext);

  if (!context) {
    throw new Error("useDateContext must be used within a DateContextProvider");
  }

  return context;
};
