import React, { useState } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Calendar } from "@/components/ui/calendar";
import { format } from 'date-fns';
import { CalendarIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { DateRange } from 'react-day-picker';

// Define types for filter state
interface AlertFilters {
  keyword: string;
  alertType: string;
  severity: string;
  dateRange: {
    from: Date | undefined;
    to: Date | undefined;
  };
  location: string;
}

export const AlertsFilter: React.FC<{
  onApplyFilters: (filters: AlertFilters) => void;
}> = ({ onApplyFilters }) => {
  const [filters, setFilters] = useState<AlertFilters>({
    keyword: '',
    alertType: '',
    severity: '',
    dateRange: { from: undefined, to: undefined },
    location: ''
  });

  const handleFilterChange = (key: keyof AlertFilters, value: string | Date | DateRange | undefined) => {
    setFilters(prev => {
      if (key === 'dateRange' && value && typeof value === 'object' && 'from' in value) {
        return {
          ...prev,
          dateRange: value as { from: Date | undefined; to: Date | undefined }
        };
      }
      return {
        ...prev,
        [key]: value
      };
    });
  };

  const handleApplyFilters = () => {
    onApplyFilters(filters);
  };

  const handleClearFilters = () => {
    const clearedFilters: AlertFilters = {
      keyword: '',
      alertType: '',
      severity: '',
      dateRange: { from: undefined, to: undefined },
      location: ''
    };
    setFilters(clearedFilters);
    onApplyFilters(clearedFilters);
  };

  return (
    <div className="flex flex-wrap gap-2 items-center mb-4">
      {/* Keyword Search */}
      <Input 
        placeholder="Search alerts" 
        value={filters.keyword}
        onChange={(e) => handleFilterChange('keyword', e.target.value)}
        className="w-64"
      />

      {/* Alert Type Dropdown */}
      <Select 
        value={filters.alertType} 
        onChange={(e) => handleFilterChange('alertType', e.target.value)}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Alert Type" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="impossible_travel">Impossible Travel</SelectItem>
          <SelectItem value="new_device">New Device</SelectItem>
        </SelectContent>
      </Select>

      {/* Severity Dropdown */}
      <Select 
        value={filters.severity} 
        onChange={(e) => handleFilterChange('severity', e.target.value)}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Severity" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="low">Low</SelectItem>
          <SelectItem value="medium">Medium</SelectItem>
          <SelectItem value="high">High</SelectItem>
        </SelectContent>
      </Select>

      {/* Date Range Picker */}
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant={'outline'}
            className={cn(
              'w-[240px] justify-start text-left font-normal',
              !filters.dateRange.from && 'text-muted-foreground'
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {filters.dateRange.from ? (
              filters.dateRange.to ? (
                <>
                  {format(filters.dateRange.from, 'LLL dd, y')} -{' '}
                  {format(filters.dateRange.to, 'LLL dd, y')}
                </>
              ) : (
                format(filters.dateRange.from, 'LLL dd, y')
              )
            ) : (
              <span>Pick a date</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0">
          <Calendar
            mode="range"
            selected={filters.dateRange}
            onSelect={(range) => handleFilterChange('dateRange', range)}
            initialFocus
          />
        </PopoverContent>
      </Popover>

      {/* Location Dropdown */}
      <Select 
        value={filters.location} 
        onChange={(e) => handleFilterChange('location', e.target.value)}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Location" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="us">United States</SelectItem>
          <SelectItem value="eu">Europe</SelectItem>
        </SelectContent>
      </Select>

      {/* Apply and Clear Buttons */}
      <div className="flex gap-2">
        <Button onClick={handleApplyFilters}>Apply Filters</Button>
        <Button variant="outline" onClick={handleClearFilters}>
          Clear All
        </Button>
      </div>
    </div>
  );
};