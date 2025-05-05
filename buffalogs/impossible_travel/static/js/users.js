document.addEventListener("DOMContentLoaded", function() {
    const initDateRangePicker = () => {
        const reportRangeElement = document.getElementById('reportrange');
        if (!reportRangeElement) return;

        const endDate = reportRangeElement.dataset.enddate ?
            moment(new Date(reportRangeElement.dataset.enddate)) :
            moment().endOf('day');
            
        const startDate = reportRangeElement.dataset.startdate ?
            moment(new Date(reportRangeElement.dataset.startdate)) :
            moment().subtract(7, 'days').startOf('day');

        $('#reportrange').daterangepicker({
            startDate: startDate,
            endDate: endDate,
            maxDate: moment().endOf('day'),
            ranges: {
                'Today': [moment().startOf('day'), moment().endOf('day')],
                'Yesterday': [moment().subtract(1, 'days').startOf('day'), moment().subtract(1, 'days').endOf('day')],
                'Last 7 Days': [moment().subtract(6, 'days').startOf('day'), moment().endOf('day')],
                'Last 30 Days': [moment().subtract(29, 'days').startOf('day'), moment().endOf('day')],
                'This Month': [moment().startOf('month'), moment().endOf('month')],
                'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
            },
            locale: {
                format: 'MMM D, YYYY'
            }
        }, function(start, end) {
            document.getElementById('startDate').value = start.format('YYYY-MM-DD');
            document.getElementById('endDate').value = end.format('YYYY-MM-DD');
            document.getElementById('analysisForm').submit();
        });


        $('#reportrange span').html(startDate.format('MMM D, YYYY') + ' - ' + endDate.format('MMM D, YYYY'));
    };

    const setupEventListeners = () => {
        const userSelect = document.getElementById('userSelect');
        if (userSelect) {
            userSelect.addEventListener('change', function() {
                document.getElementById('analysisForm').submit();
            });
        }
    };

    initDateRangePicker();
    setupEventListeners();
});