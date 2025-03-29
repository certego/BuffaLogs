//CSRF Token to be able to send update name and notes
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function post(path, params, method='post') {
    // The rest of this code assumes you are not using a library.
    // It can be made less verbose if you use one.
    const form = document.createElement('form');
    form.method = method;
    form.action = path;

    for (const key in params) {
        if (params.hasOwnProperty(key)) {
            const hiddenField = document.createElement('input');
            hiddenField.type = 'hidden';
            hiddenField.name = key;
            hiddenField.value = params[key];

            form.appendChild(hiddenField);
        }
    }

    document.body.appendChild(form);
    form.submit();
}

// This is Global variable to store grid options for access in other functions
let gridOptions;

// live alerts chart
document.addEventListener( "DOMContentLoaded", function () {

    const columns = [
        {
            field: "user",
            headerName: "Username",
            resizable: true,
            editable: true,
            sortable: true,
            unSortIcon: true,
            filter: true,
            flex: 1,
            minWidth: 100
        },
        {
            field: "timestamp",
            headerName: "Timestamp",
            resizable: true,
            sortable: true,
            unSortIcon: true,
            editable: true,
            filter: true,
            flex: 1,
            minWidth: 120
        },
        {
            field: "name",
            headerName: "Alert name",
            resizable: true,
            editable: true,
            sortable: true,
            unSortIcon: true,
            filter: true,
            flex: 1,
            minWidth: 100
        }
    ];

    function fetch_request() {
        const countrySelector = document.getElementById('countrySelector');
        const country = countrySelector ? countrySelector.value : '';
        
        let url = "/get_last_alerts";
        if (country) {
            url += `?country=${encodeURIComponent(country)}`;
        }
        
        fetch(url, {
            method: 'GET',
            headers: {
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest"
            }
        })
        .then(response => response.json())
        .then((data) => {
            const parsedData = JSON.parse(data);
            gridOptions.rowData = parsedData;
            gridOptions.api.setRowData(parsedData);
        })
        .catch(err => console.log('Request Failed', err));
    }
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
            flex: 1
        },

        //Pagination options
        pagination: true,
        paginationPageSize: 25,

        domLayout: 'autoHeight',

        //Row selection
        rowSelection: "multiple",
        suppressRowClickSelection: true,
        suppressCellSelection: true,

        enableBrowserTooltips: true,

        onGridReady: event => {
            fetch_request();

            // Handle grid size initially and when parent container resizes
            const resizeObserver = new ResizeObserver(() => {
                setTimeout(() => {
                    event.api.sizeColumnsToFit();
                }, 100);
            });

            const gridContainer = document.querySelector('.live-alerts-container');
            if (gridContainer) {
                resizeObserver.observe(gridContainer);
            }
        }
    };

    // get div to host the grid
    const eGridDiv = document.getElementById("myGrid");

    // Only create the grid if the element exists
    if (eGridDiv) {
        // new grid instance, passing in the hosting DIV and Grid Options
        new agGrid.Grid(eGridDiv, gridOptions);

        gridOptions.api.sizeColumnsToFit();

    }
})

function cb(start, end) {
    $('#reportrange span').html(start.format('MMMM D, YYYY') + ' - ' + end.format('MMMM D, YYYY'));
}

// Initialize date range picker
document.addEventListener("DOMContentLoaded", function () {
    const reportRangeElement = document.getElementById('reportrange');
    if (reportRangeElement) {
        var end = moment(new Date(reportRangeElement.getAttribute("data-enddate")));
        var start = moment(new Date(reportRangeElement.getAttribute("data-startdate")));

        $('#reportrange').daterangepicker({
            startDate: start,
            endDate: end,
            maxDate: new Date(),
            ranges: {
                'Today': [moment().utc().set({h:0, m:0, s:0}), moment().utc()],
                'Yesterday': [moment().utc().subtract(1, 'days').set({h:0, m:0, s:0}), moment().utc().subtract(1, 'days').set({h:23, m:59, s:59})],
                'Last 7 Days': [moment().utc().subtract(6, 'days'), moment().utc()],
                'Last 30 Days': [moment().utc().subtract(29, 'days'), moment().utc()],
                'This Month': [moment().utc().startOf('month'), moment().utc().endOf('month')],
                'Last Month': [moment().utc().subtract(1, 'month').startOf('month'), moment().utc().subtract(1, 'month').endOf('month')]
            }
        }, cb);
        cb(start, end);


$('#reportrange').on('apply.daterangepicker', function() {
            let start = $('#reportrange').data('daterangepicker').startDate.toDate();
            let end = $('#reportrange').data('daterangepicker').endDate.toDate();
            let date_range = parseRangeData(start, end);
            cb(date_range[0], date_range[1]);

            // POST
            const csrftoken = getCookie('csrftoken');
            let param = { "csrfmiddlewaretoken": csrftoken, "date_range": JSON.stringify(date_range) };
            post(window.location.origin + '/homepage/', param);
        });
    }
});


function parseRangeData(start_date, end_date){
    var start_tosend = moment(new Date(start_date));
    var end_tosend = moment(new Date(end_date));
    days_diff_datetime = end_tosend.diff(start_tosend, 'days');
    const date_range = [];
    date_range[0] = start_tosend;
    date_range[1] = end_tosend;
    return date_range
}

// Initialize country filter
document.addEventListener("DOMContentLoaded", function() {
    // Set up country filter
    const countrySelector = document.getElementById('countrySelector');
    const clearCountryFilter = document.getElementById('clearCountryFilter');
    
    if (countrySelector && clearCountryFilter) {
        // Fetch countries data
        fetch("/get_countries", {
            method: 'GET',
            headers: {
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest"
            }
        })
        .then(response => response.json())
        .then((data) => {
            const countries = JSON.parse(data);
            
            // Populate dropdown with countries
            countries.forEach(country => {
                const option = document.createElement('option');
                option.value = country;
                option.textContent = country;
                countrySelector.appendChild(option);
            });
        })
        .catch(err => console.log('Failed to fetch countries', err));
        
        // Apply country filter when selection changes
        countrySelector.addEventListener('change', function() {
            applyCountryFilter(this.value);
        });
        
        // Clear filter button
        clearCountryFilter.addEventListener('click', function() {
            countrySelector.value = '';
            applyCountryFilter('');
        });
    }
});

function applyCountryFilter(country) {
    const csrftoken = getCookie('csrftoken');
    
    // Apply filter to grid
    if (gridOptions && gridOptions.api) {
        if (country) {
            // Filter the current grid data
            gridOptions.api.setQuickFilter(country);
        } else {
            // Clear filter
            gridOptions.api.setQuickFilter('');
        }
    }
    
    // Update world map and other visualizations
    fetch("/filter_by_country", {
        method: 'POST',
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrftoken
        },
        body: JSON.stringify({ country: country })
    })
    .then(response => response.json())
    .then((data) => {
        try {
            // Update world map
            const worldMapContainer = document.querySelector('.world-map-container figure embed');
            console.log("Map container:", worldMapContainer);
            console.log("Map data:", data.world_map_context);
            
            if (worldMapContainer && data.world_map_context) {
                worldMapContainer.setAttribute('src', data.world_map_context);
            } else {
                console.error("Either map container or map data is missing");
            }
            
            // Update other charts if needed
            // ...rest of your code
        } catch (error) {
            console.error("Error updating visualizations:", error);
        }
    })
    .catch(err => console.log('Filter request failed', err));
}