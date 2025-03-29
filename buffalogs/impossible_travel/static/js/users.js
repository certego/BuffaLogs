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
    searchInput.id = 'user-search-filter';
    searchInput.placeholder = 'Search users...';
    searchInput.style.padding = '8px';
    searchInput.style.marginRight = '10px';
    searchInput.style.borderRadius = '4px';
    searchInput.style.border = '1px solid #444';
    searchInput.style.backgroundColor = '#3a3a3a';
    searchInput.style.color = '#dee2e6';
    
    // Create risk score filter
    const riskScoreFilter = document.createElement('select');
    riskScoreFilter.id = 'risk-score-filter';
    riskScoreFilter.style.padding = '8px';
    riskScoreFilter.style.marginRight = '10px';
    riskScoreFilter.style.borderRadius = '4px';
    riskScoreFilter.style.border = '1px solid #444';
    riskScoreFilter.style.backgroundColor = '#3a3a3a';
    riskScoreFilter.style.color = '#dee2e6';
    
    // Default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'All Risk Levels';
    riskScoreFilter.appendChild(defaultOption);
    
    // Add risk level options
    const riskLevels = ['Low', 'Medium', 'High'];
    riskLevels.forEach(level => {
        const option = document.createElement('option');
        option.value = level;
        option.textContent = level;
        riskScoreFilter.appendChild(option);
    });
    
    // Create login date filter
    const loginDateContainer = document.createElement('div');
    loginDateContainer.style.display = 'inline-block';
    loginDateContainer.style.marginRight = '10px';
    
    const loginDateInput = document.createElement('input');
    loginDateInput.type = 'text';
    loginDateInput.id = 'login-date-filter';
    loginDateInput.placeholder = 'Last Login Date';
    loginDateInput.style.padding = '8px';
    loginDateInput.style.borderRadius = '4px';
    loginDateInput.style.border = '1px solid #444';
    loginDateInput.style.backgroundColor = '#3a3a3a';
    loginDateInput.style.color = '#dee2e6';
    loginDateContainer.appendChild(loginDateInput);
    
    // Create clear filters button
    const clearButton = document.createElement('button');
    clearButton.id = 'clear-user-filters';
    clearButton.textContent = 'Clear All';
    clearButton.style.padding = '8px 15px';
    clearButton.style.borderRadius = '4px';
    clearButton.style.border = '1px solid #444';
    clearButton.style.backgroundColor = '#343a40';
    clearButton.style.color = '#dee2e6';
    clearButton.style.cursor = 'pointer';
    
    // Add active filters indicator
    const activeFilters = document.createElement('div');
    activeFilters.id = 'active-user-filters';
    activeFilters.style.marginTop = '10px';
    activeFilters.style.color = '#dee2e6';
    activeFilters.style.fontSize = '0.9rem';
    
    // Append all elements to filter container
    filterContainer.appendChild(searchInput);
    filterContainer.appendChild(riskScoreFilter);
    filterContainer.appendChild(loginDateContainer);
    filterContainer.appendChild(clearButton);
    filterContainer.appendChild(activeFilters);
    
    // Insert filter container before the grid
    const gridDiv = document.getElementById('myGrid');
    gridDiv.parentNode.insertBefore(filterContainer, gridDiv);
    
    const columns = [
        { 
            field: "user",
            headerName: "Username",
            resizable: true,
            editable: true,
            sortable: true,
            unSortIcon: true,
            filter: true,
        }, 
        { 
            field: "last_login",
            headerName: "Last Login",
            resizable: true,
            sortable: true,
            unSortIcon: true,
            editable: true,
            filter: true,
        }, 
        { 
            field: "risk_score",
            headerName: "Risk Score",
            resizable: true,
            editable: true,
            sortable: true,
            unSortIcon: true,
            filter: true,
        }, 
        { 
            field: "logins_num",
            headerName: "Unique Logins",
            cellRenderer: function(params) {
                const eDiv = document.createElement('a');
                eDiv.setAttribute("href",`${window.location.href}${params.data.id}/unique_logins`);
                eDiv.innerText = `unique logins (${params.data.logins_num})`;
                return eDiv;
            },
            resizable: true,
            sortable: true,
            unSortIcon: true,
        },
        {
            headerName: "All Logins",
            cellRenderer: function(params) {
                const eDiv = document.createElement('a');
                eDiv.setAttribute("href",`${window.location.href}${params.data.id}/all_logins`);
                eDiv.innerText = `All logins`;
                return eDiv;
            },
            resizable: true,
        }, 
        { 
            field: "alerts_num",
            headerName: "Alerts",
            cellRenderer: function(params) {
                const eDiv = document.createElement('a');
                eDiv.setAttribute("href",`${window.location.href}${params.data.id}/alerts`);
                eDiv.innerText = `alerts (${params.data.alerts_num})`;
                return eDiv;
            },
            resizable: true,
            sortable: true,
            unSortIcon: true,
        },
    ];

    // Store all fetched data for filtering
    let allUserData = [];

    function fetch_request() {
        fetch("/get_users", {
            method: 'GET', 
            headers: {
                "Accept": "application/json", 
                "X-Requested-With": "XMLHttpRequest"
            }
        })
        .then(response => response.json())
        .then((data) => {
            const parsedData = JSON.parse(data);
            allUserData = parsedData;
            
            // Set initial grid data
            gridOptions.api.setRowData(parsedData);
            
            // Initialize date range picker
            if (typeof $ !== 'undefined' && $.fn.daterangepicker) {
                $('#login-date-filter').daterangepicker({
                    autoUpdateInput: false,
                    locale: {
                        cancelLabel: 'Clear'
                    }
                });
                
                $('#login-date-filter').on('apply.daterangepicker', function(ev, picker) {
                    $(this).val(picker.startDate.format('MM/DD/YYYY') + ' - ' + picker.endDate.format('MM/DD/YYYY'));
                    filterData();
                    updateActiveFilters();
                });
                
                $('#login-date-filter').on('cancel.daterangepicker', function(ev, picker) {
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
        const riskLevel = riskScoreFilter.value;
        const loginDateRange = loginDateInput.value;
        
        let startDate, endDate;
        if (loginDateRange) {
            const dates = loginDateRange.split(' - ');
            if (dates.length === 2) {
                startDate = new Date(dates[0]);
                endDate = new Date(dates[1]);
                endDate.setHours(23, 59, 59); // Include the entire end day
            }
        }
        
        const filteredData = allUserData.filter(user => {
            // Search term filter
            const matchesSearch = !searchTerm || 
                (user.user && user.user.toLowerCase().includes(searchTerm));
            
            // Risk level filter
            const matchesRiskLevel = !riskLevel || 
                (user.risk_score && user.risk_score.includes(riskLevel));
            
            // Login date filter
            let matchesLoginDate = true;
            if (startDate && endDate && user.last_login) {
                const loginDate = new Date(user.last_login);
                matchesLoginDate = loginDate >= startDate && loginDate <= endDate;
            }
            
            return matchesSearch && matchesRiskLevel && matchesLoginDate;
        });
        
        gridOptions.api.setRowData(filteredData);
    }
    
    // Update active filters indicator
    function updateActiveFilters() {
        const filters = [];
        
        if (searchInput.value) {
            filters.push(`Username: "${searchInput.value}"`);
        }
        
        if (riskScoreFilter.value) {
            filters.push(`Risk Level: ${riskScoreFilter.value}`);
        }
        
        if (loginDateInput.value) {
            filters.push(`Login Date: ${loginDateInput.value}`);
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
    
    riskScoreFilter.addEventListener('change', () => {
        filterData();
        updateActiveFilters();
    });
    
    clearButton.addEventListener('click', () => {
        searchInput.value = '';
        riskScoreFilter.value = '';
        loginDateInput.value = '';
        gridOptions.api.setRowData(allUserData);
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