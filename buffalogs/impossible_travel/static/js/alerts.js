// Enhanced alerts.js with filtering capabilities
document.addEventListener("DOMContentLoaded", function () {
    // Create filter container
    const filterContainer = document.createElement('div');
    filterContainer.className = 'filter-container';
    filterContainer.style.margin = '20px 0';
    filterContainer.style.padding = '15px';
    filterContainer.style.backgroundColor = '#2d353c';
    filterContainer.style.borderRadius = '10px';
    
    // Create search input
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.id = 'search-filter';
    searchInput.placeholder = 'Search alerts...';
    searchInput.style.padding = '8px';
    searchInput.style.marginRight = '10px';
    searchInput.style.borderRadius = '4px';
    searchInput.style.border = '1px solid #444';
    searchInput.style.backgroundColor = '#3a3a3a';
    searchInput.style.color = '#dee2e6';
    
    // Create rule type filter
    const ruleTypeFilter = document.createElement('select');
    ruleTypeFilter.id = 'rule-type-filter';
    ruleTypeFilter.style.padding = '8px';
    ruleTypeFilter.style.marginRight = '10px';
    ruleTypeFilter.style.borderRadius = '4px';
    ruleTypeFilter.style.border = '1px solid #444';
    ruleTypeFilter.style.backgroundColor = '#3a3a3a';
    ruleTypeFilter.style.color = '#dee2e6';
    
    // Default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'All Alert Types';
    ruleTypeFilter.appendChild(defaultOption);
    
    // Create date range picker
    const dateRangeContainer = document.createElement('div');
    dateRangeContainer.style.display = 'inline-block';
    dateRangeContainer.style.marginRight = '10px';
    
    const dateRangeInput = document.createElement('input');
    dateRangeInput.type = 'text';
    dateRangeInput.id = 'date-range-filter';
    dateRangeInput.placeholder = 'Date Range';
    dateRangeInput.style.padding = '8px';
    dateRangeInput.style.borderRadius = '4px';
    dateRangeInput.style.border = '1px solid #444';
    dateRangeInput.style.backgroundColor = '#3a3a3a';
    dateRangeInput.style.color = '#dee2e6';
    dateRangeContainer.appendChild(dateRangeInput);
    
    // Create clear filters button
    const clearButton = document.createElement('button');
    clearButton.id = 'clear-filters';
    clearButton.textContent = 'Clear All';
    clearButton.style.padding = '8px 15px';
    clearButton.style.borderRadius = '4px';
    clearButton.style.border = '1px solid #444';
    clearButton.style.backgroundColor = '#343a40';
    clearButton.style.color = '#dee2e6';
    clearButton.style.cursor = 'pointer';
    
    // Add active filters indicator
    const activeFilters = document.createElement('div');
    activeFilters.id = 'active-filters';
    activeFilters.style.marginTop = '10px';
    activeFilters.style.color = '#dee2e6';
    activeFilters.style.fontSize = '0.9rem';
    
    // Append all elements to filter container
    filterContainer.appendChild(searchInput);
    filterContainer.appendChild(ruleTypeFilter);
    filterContainer.appendChild(dateRangeContainer);
    filterContainer.appendChild(clearButton);
    filterContainer.appendChild(activeFilters);
    
    // Insert filter container before the grid
    const gridDiv = document.getElementById('myGrid');
    gridDiv.parentNode.insertBefore(filterContainer, gridDiv);

    const columns = [
        { 
            field: "timestamp",
            headerName: "Login Timestamp",
            resizable: true,
            sortable: true,
            unSortIcon: true,
            editable: true,
            filter: true,
        },
        { 
            field: "rule_name",
            headerName: "Alert Rule Name",
            resizable: true,
            filter: true,
        },
        {
            field: "rule_desc",
            headerName: "Alert Rule Description",
            resizable: true,
            filter: true,
            minWidth: 900,
        },
    ];

    // Store all fetched data for filtering
    let allAlertData = [];

    function fetch_request() {
        fetch(window.location.href+"/get_alerts", {
            method: 'GET', 
            headers: {
                "Accept":"application/json", 
                "X-Requested-With":"XMLHttpRequest"
            }
        })
        .then(response => response.json())
        .then((data) => {
            const parsedData = JSON.parse(data);
            allAlertData = parsedData;
            
            // Populate rule type filter options
            const ruleTypes = new Set();
            parsedData.forEach(alert => {
                if (alert.rule_name) {
                    ruleTypes.add(alert.rule_name);
                }
            });
            
            ruleTypes.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                ruleTypeFilter.appendChild(option);
            });
            
            // Set initial grid data
            gridOptions.api.setRowData(parsedData);
            
            // Initialize date range picker
            if (typeof $ !== 'undefined' && $.fn.daterangepicker) {
                $('#date-range-filter').daterangepicker({
                    autoUpdateInput: false,
                    locale: {
                        cancelLabel: 'Clear'
                    }
                });
                
                $('#date-range-filter').on('apply.daterangepicker', function(ev, picker) {
                    $(this).val(picker.startDate.format('MM/DD/YYYY') + ' - ' + picker.endDate.format('MM/DD/YYYY'));
                    filterData();
                    updateActiveFilters();
                });
                
                $('#date-range-filter').on('cancel.daterangepicker', function(ev, picker) {
                    $(this).val('');
                    filterData();
                    updateActiveFilters();
                });
            }
        })
        .catch(err => console.log('Request Failed', err));
    }

    // Filter function
    function filterData() {
        const searchTerm = searchInput.value.toLowerCase();
        const ruleType = ruleTypeFilter.value;
        const dateRange = dateRangeInput.value;
        
        let startDate, endDate;
        if (dateRange) {
            const dates = dateRange.split(' - ');
            if (dates.length === 2) {
                startDate = new Date(dates[0]);
                endDate = new Date(dates[1]);
                endDate.setHours(23, 59, 59); // Include the entire end day
            }
        }
        
        const filteredData = allAlertData.filter(alert => {
            // Search term filter
            const matchesSearch = !searchTerm || 
                (alert.rule_name && alert.rule_name.toLowerCase().includes(searchTerm)) || 
                (alert.rule_desc && alert.rule_desc.toLowerCase().includes(searchTerm));
            
            // Rule type filter
            const matchesRuleType = !ruleType || (alert.rule_name === ruleType);
            
            // Date filter
            let matchesDate = true;
            if (startDate && endDate) {
                const alertDate = new Date(alert.timestamp);
                matchesDate = alertDate >= startDate && alertDate <= endDate;
            }
            
            return matchesSearch && matchesRuleType && matchesDate;
        });
        
        gridOptions.api.setRowData(filteredData);
    }
    
    // Update active filters indicator
    function updateActiveFilters() {
        const filters = [];
        
        if (searchInput.value) {
            filters.push(`Search: "${searchInput.value}"`);
        }
        
        if (ruleTypeFilter.value) {
            filters.push(`Type: ${ruleTypeFilter.value}`);
        }
        
        if (dateRangeInput.value) {
            filters.push(`Date: ${dateRangeInput.value}`);
        }
        
        if (filters.length > 0) {
            activeFilters.textContent = 'Active Filters: ' + filters.join(' | ');
            activeFilters.style.display = 'block';
        } else {
            activeFilters.style.display = 'none';
        }
    }
    
    // Add event listeners for filters
    searchInput.addEventListener('input', () => {
        filterData();
        updateActiveFilters();
    });
    
    ruleTypeFilter.addEventListener('change', () => {
        filterData();
        updateActiveFilters();
    });
    
    clearButton.addEventListener('click', () => {
        searchInput.value = '';
        ruleTypeFilter.value = '';
        dateRangeInput.value = '';
        gridOptions.api.setRowData(allAlertData);
        activeFilters.style.display = 'none';
    });

    // Grid options (to customize grid)
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

        suppressMultiSort: true,
        accentedSort: true,

        defaultColDef: {
            resizable: false,
            editable: false,
            filter: false,
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
            fetch_request();
            event.api.sizeColumnsToFit();
        }
    };

    // get div to host the grid
    const eGridDiv = document.getElementById("myGrid");
    // new grid instance, passing in the hosting DIV and Grid Options
    new agGrid.Grid(eGridDiv, gridOptions);   

    gridOptions.api.sizeColumnsToFit();
});