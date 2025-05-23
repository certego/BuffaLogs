document.addEventListener( "DOMContentLoaded", function () {

    const columns = [
        { 
            field: "timestamp",
            headerName: "Login Timestamp",
            resizable: true,
            sortable: true,
            unSortIcon: true,
            editable: false,
            filter: true,
            flex: 1,
        },
        { 
            field: "created",
            headerName: "Created At",
            resizable: true,
            sortable: true,
            filter: true,
            editable: false,
            flex: 1,
        },
        {
            field: "notified",
            headerName: "Notified",
            resizable: true,
            sortable: true,
            filter: true,
            editable: false,
            width: 130,
            cellRenderer: (params) => params.value ? 'Yes' : 'No',
        },
        {
            field: "triggered_by",
            headerName: "Triggered By",
            resizable: true,
            filter: true,
            editable: false,
            flex: 1,
        },
        { 
            field: "rule_name",
            headerName: "Name",
            resizable: true,
            filter: true,
            editable: false,
            flex: 1,
        },
        {
            field: "rule_desc",
            headerName: "Description",
            resizable: true,
            filter: true,
            editable: false,
            minWidth: 300,
            flex: 2,
        },
        {
            field: "is_vip",
            headerName: "VIP",
            resizable: true,
            filter: true,
            width: 130,
            editable: false,
            cellRenderer: (params) => params.value ? 'VIP' : '—',
        },
        {
          field: "severity_type",
          headerName: "Severity",
          resizable: true,
          filter: true,
          editable: false,
          hide:true,
          width: 130,
        },

        {
          field: "country",
          headerName: "Country",
          resizable: true,
          filter: true,
          editable: false,
          hide:true,
          width: 130,
        },
    ];

  let allData = [];
  let alertTypes = new Set();
  let severity = new Set();
  let countries = new Set();
  let activeFilters = {
    search: "",
    alertType: "",
    severity: "",
    country:"",
    vip: "",
    startDate: null,
    endDate: null
  };

  function fetchAlerts() {
    fetch(window.location.href + "/get_alerts", {
      method: 'GET',
      headers: {
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest"
      }
    })
    .then(response => response.json())
    .then((data) => {
      console.log("Fetched data:", data);
      allData = data;
      
      data.forEach(item => {
        if (item.rule_name) alertTypes.add(item.rule_name);
      });

      data.forEach(item=> {
        if (item.severity_type) severity.add(item.severity_type)
      });

      data.forEach(item=>{
        if(item.country) countries.add(item.country)
      })
      
      const alertTypeSelect = document.getElementById('alert-type-filter');
      alertTypeSelect.innerHTML = '<option value="">All Types</option>';
      Array.from(alertTypes).sort().forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type;
        alertTypeSelect.appendChild(option);
      });

      const severity_type = document.getElementById('severity-filter');
      severity_type.innerHTML = '<option value="">All Severities</option>';
      Array.from(severity).sort().forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type;
        severity_type.appendChild(option);
      });

      const country = document.getElementById('country-filter');
      country.innerHTML = '<option value="">Country</option>';
      Array.from(countries).sort().forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type;
        country.appendChild(option);
      });
 
      
      // Set initial grid data
      gridOptions.api.setRowData(data);
    })
    .catch(err => console.log('Request Failed', err));
  }

  function applyFilters() {
    const filteredData = allData.filter(item => {
      if (activeFilters.search && !Object.values(item).some(val => 
        val && val.toString().toLowerCase().includes(activeFilters.search.toLowerCase())
      )) {
        return false;
      }
      
      if (activeFilters.alertType && item.rule_name !== activeFilters.alertType) {
        return false;
      }
      
      if (activeFilters.severity && item.severity_type !== activeFilters.severity) {
        return false;
      }

      if(activeFilters.country && item.country !== activeFilters.country) {
        return false;
      }
      
      if (activeFilters.vip) {
        const isVip = activeFilters.vip === "true";
        if (item.is_vip !== isVip) {
          return false;
        }
      }
      
      if (activeFilters.startDate && activeFilters.endDate) {
        const itemDate = new Date(item.created);
        if (itemDate < activeFilters.startDate || itemDate > activeFilters.endDate) {
          return false;
        }
      }
            
      return true;
    });
    
    gridOptions.api.setRowData(filteredData);
    updateActiveFiltersDisplay();
  }

  function updateActiveFiltersDisplay() {
    const container = document.getElementById('active-filters-container');
    container.innerHTML = '';
    
    // Helper function to create a filter badge
    function createBadge(filterName, filterValue, displayValue) {
      const badge = document.createElement('span');
      badge.className = 'badge bg-grey text-light filter-badge p-2 m-1';
      badge.innerHTML = `${filterName}: ${displayValue} <button type="button" class="btn-close btn-close-white btn-sm ms-2" aria-label="Close"></button>`;
      
      badge.querySelector('.btn-close').addEventListener('click', () => {
        activeFilters[filterValue] = filterValue === 'startDate' || filterValue === 'endDate' ? null : "";
        
        if (filterValue === 'startDate' || filterValue === 'endDate') {
          activeFilters.startDate = null;
          activeFilters.endDate = null;
          dateRangePicker.clear();
        } else {
          const element = document.getElementById(`${filterValue}-filter`);
          if (element) element.value = "";
        }
        
        applyFilters();
      });
      
      return badge;
    }
    
    if (activeFilters.search) {
      container.appendChild(createBadge('Search', 'search', activeFilters.search));
    }
    
    if (activeFilters.alertType) {
      container.appendChild(createBadge('Alert Type', 'alertType', activeFilters.alertType));
    }
    
    if (activeFilters.severity) {
      container.appendChild(createBadge('Severity', 'severity', activeFilters.severity));
    }

    if (activeFilters.country) {
      container.appendChild(createBadge('Country', 'country', activeFilters.country));
    }
    
    if (activeFilters.vip) {
      container.appendChild(createBadge('VIP Status', 'vip', activeFilters.vip === 'true' ? 'VIP Only' : 'Non-VIP Only'));
    }
    
    if (activeFilters.startDate && activeFilters.endDate) {
      const dateRange = `${activeFilters.startDate.toLocaleDateString()} - ${activeFilters.endDate.toLocaleDateString()}`;
      container.appendChild(createBadge('Date Range', 'startDate', dateRange));
    }
    
  }

    const gridOptions = {
        columnDefs: columns,
        rowData: undefined,
        //To mantain column order even if updated data has different order
        maintainColumnOrder: true,
        //To avoid column movement with mouse
        suppressMovableColumns: true,

        stopEditingWhenCellsLoseFocus: true,
        enterMovesDownAfterEdit: true,
        undoRedoCellEditing: true,
        undoRedoCellEditingLimit: 10,
        cacheQuickFilter: true,

        suppressMultiSort:true,
        accentedSort:true,

        defaultColDef:{
            resizable: false,
            editable:false,
            filter: true,
        },

        //Pagination options
        pagination: true,
        paginationPageSize: 20,

        domLayout: 'autoHeight',

        //Row selection
        rowSelection: "multiple",
        suppressRowClickSelection: true,
        suppressCellSelection: true,

        enableBrowserTooltips: true,

        onGridReady: event => {
          fetchAlerts();
        }
      };

  const eGridDiv = document.getElementById("myGrid");
  new agGrid.Grid(eGridDiv, gridOptions);
  gridOptions.api.sizeColumnsToFit();

  const dateRangePicker = flatpickr("#date-range", {
    mode: "range",
    dateFormat: "Y-m-d",
    onChange: function(selectedDates) {
      if (selectedDates.length === 2) {
        activeFilters.startDate = selectedDates[0];
        activeFilters.endDate = selectedDates[1];
        applyFilters();
      }
    }
  });

  document.getElementById('search-button').addEventListener('click', () => {
    activeFilters.search = document.getElementById('search-input').value;
    applyFilters();
  });

  document.getElementById('search-input').addEventListener('keyup', (e) => {
    if (e.key === 'Enter') {
      activeFilters.search = e.target.value;
      applyFilters();
    }
  });

  document.getElementById('alert-type-filter').addEventListener('change', (e) => {
    activeFilters.alertType = e.target.value;
    applyFilters();
  });

  document.getElementById('severity-filter').addEventListener('change', (e) => {
    activeFilters.severity = e.target.value;
    applyFilters();
  });


  document.getElementById('country-filter').addEventListener('change', (e) => {
  activeFilters.country = e.target.value;
  applyFilters();
  });

  document.getElementById('vip-filter').addEventListener('change', (e) => {
    activeFilters.vip = e.target.value;
    applyFilters();
  });


  document.getElementById('clear-date-range').addEventListener('click', () => {
    dateRangePicker.clear();
    activeFilters.startDate = null;
    activeFilters.endDate = null;
    applyFilters();
  });

  document.getElementById('clear-all-filters').addEventListener('click', () => {
    activeFilters = {
      search: "",
      alertType: "",
      severity: "",
      country:"",
      vip: "",
      startDate: null,
      endDate: null
    };
    
    document.getElementById('search-input').value = "";
    document.getElementById('alert-type-filter').value = "";
    document.getElementById('severity-filter').value = "";
    document.getElementById('country-filter').value = "";
    document.getElementById('vip-filter').value = "";
    dateRangePicker.clear();
    
    applyFilters();
  });
});