document.addEventListener( "DOMContentLoaded", function () {

    const columns = [
        { 
            field: "timestamp",
            headerName: "Login Timestamp",
            resizable: true,
            maxWidth: 250,
            sortable: true,
            unSortIcon: true,
            filter: true,
        }, 
        { 
            field: "country",
            headerName: "Country",
            resizable: true,
            maxWidth: 250,
            filter: true,
            sortable: true,
            unSortIcon: true,
        }, 
        { 
            field: "latitude",
            headerName: "Latitude",
            resizable: true,
            maxWidth: 150,
        },
        { 
            field: "longitude",
            headerName: "Longitude",
            resizable: true,
            maxWidth: 150,
        },
        { 
            field: "user_agent",
            headerName: "User Agent",
            resizable: true,
            minWidth: 1000,
            filter: true,
            sortable: true,
            unSortIcon: true,
        }, 
    ]

    function fetch_request() {
        fetch(window.location.href+"/get_all_logins", {method: 'GET', headers: {"Accept":"application/json", 
            "X-Requested-With":"XMLHttpRequest"}})
        // gestisci il successo
        .then(response => response.json())  // converti a json
        .then((data) => {
            console.log(data);
            gridOptions.rowData = (JSON.parse(data));   //JSON.parse(data)
            gridOptions.api.setRowData(JSON.parse(data));
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





