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
            sortable:  true,
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
                console.log(params)
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
    ]

    function fetch_request() {
        fetch("/get_users", {method: 'GET', headers: {"Accept":"application/json", 
            "X-Requested-With":"XMLHttpRequest"}})
        // gestisci il successo
        .then(response => response.json())  // converti a json
        .then((data) => {
            gridOptions.rowData = (JSON.parse(data));
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

        //Performance
        

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

