// Function to initialize charts
function initializeChart(chartId, chartData) {
    var ctx = document.getElementById(chartId).getContext('2d');
    var chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: chartData.datasets.map(dataset => ({
                label: dataset.label,
                data: dataset.data,
                borderColor: dataset.borderColor,
                borderWidth: dataset.borderWidth,
                fill: dataset.fill
            }))
        },
        options: {
            scales: {
                x: [{
                    type: 'time',
                    time: {
                        unit: 'minute'
                    }
                }],
                y: [{
                    ticks: {
                        beginAtZero: true
                    }
                }]
            }
        }
    });
    return chart;
}

// Function to fetch and initialize charts on page load
function fetchAndInitializeCharts() {

    fetchChartData('/waiting_area_data', 'waitingAreaChart');
    fetchChartData('/customs_area_data', 'customsAreaChart');
}

// Function to fetch chart data
function fetchChartData(url, chartId) {
    fetch(url)
        .then(response => response.json())
        .then(chartData => {
            window[chartId] = initializeChart(chartId, chartData);
        });
    applyDateFilter();
}

// Apply Date Filter function
function updateCharts(data) {
    console.log('Received data:', data);

    console.log('Updating waitingAreaChart');
    updateChart(window.waitingAreaChart, data.waiting_area);
    console.log('Updating customsAreaChart');
    updateChart(window.customsAreaChart, data.customs_area);
}

function updateHtmlElements(statistics) {
    console.log('Received statistics:', statistics);

    // Check if the received statistics are empty
    if ($.isEmptyObject(statistics)) {
        // No data received, update HTML with default values
        updateHtmlElement('#avgValue', 'No Data Yet');
        updateHtmlElement('#peakValue', 'No Data Yet');
        updateHtmlElement('#occupancyRateValue', 'No Data Yet');
        updateHtmlElement('#turnoverRateValue', 'No Data Yet');
        updateHtmlElement('#avgWaitTimeValue', 'No Data Yet');
        updateHtmlElement('#avgCustomOccupancyValue', 'No Data Yet');
        updateHtmlElement('#peakCustomOccupancyValue', 'No Data Yet');
        updateHtmlElement('#avgCustomFlowRateValue', 'No Data Yet');
        updateHtmlElement('#avgCustomPassengerTurnaroundTimeValue', 'No Data Yet');
        updateHtmlElement('#avgCustomWaitTimeValue', 'No Data Yet');
    } else {
        // Data received, update HTML with the received statistics

        // Example: Average Occupancy
        updateHtmlElement('#avgValue', statistics.avg_occupancy_waiting + '%');
        // Example: Peak Occupancy
        updateHtmlElement('#peakValue', statistics.peak_occupancy_waiting + '%');
        updateHtmlElement('#occupancyRateValue', statistics.occupancy_rate_waiting + '%');
        updateHtmlElement('#turnoverRateValue', statistics.seat_turnover_rate_waiting + '%');
        updateHtmlElement('#avgWaitTimeValue', statistics.avg_wait_time_waiting + '%');

        // Update customs area statistics
        updateHtmlElement('#avgCustomOccupancyValue', statistics.avg_occupancy_custom + '%');
        updateHtmlElement('#peakCustomOccupancyValue', statistics.peak_occupancy_custom + '%');
        updateHtmlElement('#avgCustomFlowRateValue', statistics.avg_flow_rate_custom + '%');
        updateHtmlElement('#avgCustomPassengerTurnaroundTimeValue', statistics.avg_passenger_turnaround_time_custom + '%');
        updateHtmlElement('#avgCustomWaitTimeValue', statistics.avg_wait_time_custom + '%');
    }
}

function updateHtmlElement(selector, value) {
    // Update the HTML element with the provided value
    $(selector).text(value);
}

function applyDateFilter() {
    var startDate = $('#dateRangeFilter').data('daterangepicker').startDate.format('YYYY-MM-DD');
    var endDate = $('#dateRangeFilter').data('daterangepicker').endDate.format('YYYY-MM-DD');

    console.log('Selected Start Date:', startDate);
    console.log('Selected End Date:', endDate);

    // Make an AJAX request to the Flask route with start_date and end_date for updating charts
    $.ajax({
        url: '/get_date_range',
        method: 'GET',
        data: { start_date: startDate, end_date: endDate },
        success: function (data) {
            updateCharts(data);
        },
        error: function (error) {
            console.error('Error applying filter:', error);
        }
    });

    // Make an AJAX request to the Flask route with start_date and end_date for updating HTML elements
    $.ajax({
        url: '/get_statistics',
        method: 'GET',
        data: { start_date: startDate, end_date: endDate },
        success: function (statistics) {
            updateHtmlElements(statistics);
        },
        error: function (error) {
            console.error('Error fetching statistics:', error);
        }
    });
}


// Event listener for Apply Filter button
$('.applyButton').click(function () {
    applyDateFilter();
});

// Event listener for Reset Filter button
$('.resetButton').click(function () {
    // Reset the DateRangePicker
    $('#dateRangeFilter').data('daterangepicker').setStartDate(moment());
    $('#dateRangeFilter').data('daterangepicker').setEndDate(moment());

    // Disable the single date filter
    $('#singleDateFilter').val('');
    $('#singleDateFilter').prop('disabled', false);

    // Enable the date range filter
    $('#dateRangeFilter').prop('disabled', false);
});

// Initialize DateRangePicker
$(function () {
    $('#dateRangeFilter').daterangepicker();

    // Apply date filter on page load
    applyDateFilter();

    // Fetch and initialize charts on page load
    fetchAndInitializeCharts();
});


// Function to update charts with new data
function updateChart(chart, newData) {
    chart.data.labels = newData.labels;
    chart.data.datasets.forEach((dataset, index) => {
        dataset.data = newData.datasets[index].data;
    });
    chart.update();
}
