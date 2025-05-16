document.addEventListener( "DOMContentLoaded", function () {

    const columns = [
        { 
            field: "timestamp",
            headerName: "Login Timestamp",
            resizable: true,
            sortable: true,
            unSortIcon: true,
            editable: false,
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
    ];
    

    function fetch_request() {
        fetch(window.location.href+"/get_alerts", {method: 'GET', headers: {"Accept":"application/json", 
            "X-Requested-With":"XMLHttpRequest"}})
        // gestisci il successo
        .then(response => response.json())  // converti a json
        .then((data) => {
            console.log(data);
            gridOptions.api.setRowData(data);
        })
        
        .catch(err => console.log('Request Failed', err)); // gestisci gli errori
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

        suppressMultiSort:true,
        accentedSort:true,

        defaultColDef:{
            resizable: false,
            editable:false,
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
        }
    };

    // get div to host the grid
    const eGridDiv = document.getElementById("myGrid");
    // new grid instance, passing in the hosting DIV and Grid Options
    new agGrid.Grid(eGridDiv, gridOptions);   

    gridOptions.api.sizeColumnsToFit();
})





