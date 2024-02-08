// Function to initialize charts
function initializeChart(chartId, chartData) {
    // Get the canvas element by its ID
    var ctx = document.getElementById(chartId).getContext('2d');
    
    // Determine the chart type based on the chart ID
    var chartType = chartId === 'waitingAreaChart' ? 'bar' : 'line';
    
    // Extract the line dataset separately (for line charts)
    var lineDataset = chartData.datasets.find(dataset => dataset.label === 'Entrance Point Count (Customs Area)');

    // Remove the line dataset temporarily (to render other datasets first)
    var datasetsWithoutLine = chartData.datasets.filter(dataset => dataset.label !== 'Entrance Point Count (Customs Area)');

    // Create a new Chart.js instance
    var chart = new Chart(ctx, {
        type: chartType,
        data: {
            labels: chartData.labels,
            datasets: datasetsWithoutLine.map(dataset => ({
                // Map each dataset to Chart.js dataset format
                label: dataset.label,
                data: dataset.data,
                borderColor: dataset.borderColor,
                borderWidth: dataset.borderWidth,
                backgroundColor: dataset.backgroundColor,
                fill: dataset.fill,
                // Hide certain datasets initially based on their labels
                hidden: dataset.label === 'Total Seats (Waiting Area)' || dataset.label === 'Total People (Waiting Area)'
            })),
        },
        options: {
            // Chart options (e.g., title, responsiveness, scales, legend)
            plugins: {
                title: {
                    display: true,
                    // Set chart title based on the chart ID
                    text: chartId === 'waitingAreaChart' ? 'Stacked Bar Chart - Waiting Area' : 'Line Chart - Customs Area'
                },
            },
            responsive: true,
            scales: {
                x: {
                    stacked: chartType === 'bar',  // Enable stacking for x-axis only for bar charts
                },
                y: {
                    stacked: chartType === 'bar',  // Enable stacking for y-axis only for bar charts
                }
            },
            legend: {
                onClick: (e, legendItem) => {
                    // Toggle visibility on legend item click
                    var index = legendItem.datasetIndex;
                    var chart = e.chart;
                    var meta = chart.getDatasetMeta(index);

                    // Toggle visibility
                    meta.hidden = meta.hidden === null ? !chart.data.datasets[index].hidden : null;

                    // Update the chart
                    chart.update();
                }
            },
            elements: {
                line: {
                    tension: 0.4  // Adjust tension for line chart
                }
            }
        }
    });

    // Add the line dataset back to the chart (for line charts)
    if (chartType === 'line' && lineDataset) {
        chart.data.datasets.push(lineDataset);
    }

    return chart; // Return the created chart instance
}





// Function to fetch and initialize charts on page load
function fetchAndInitializeCharts() {
    // Fetch chart data for Waiting Area and Customs Area
    fetchChartData('/waiting_area_data', 'waitingAreaChart');
    fetchChartData('/customs_area_data', 'customsAreaChart');
}

// Function to fetch chart data from the server
function fetchChartData(url, chartId) {
    // Fetch data from the specified URL
    fetch(url)
        .then(response => response.json()) // Parse response as JSON
        .then(chartData => {
            // Initialize the chart using the fetched data
            window[chartId] = initializeChart(chartId, chartData);
        });
    applyDateFilter(); // Apply date filter after fetching chart data
}

// Apply Date Filter function
function updateCharts(data) {
    console.log('Received data:', data);

    // Update waiting area chart
    console.log('Updating waitingAreaChart');
    updateChart(window.waitingAreaChart, data.waiting_area);

    // Update customs area chart
    console.log('Updating customsAreaChart');
    updateChart(window.customsAreaChart, data.customs_area);
}


// Function to update HTML elements with statistics data
function updateHtmlElements(statistics) {
    console.log('Received statistics:', statistics);

    // Check if the received statistics object is empty
    if ($.isEmptyObject(statistics)) {
        // If no data is received, update HTML with default values
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
        // If data is received, update HTML with the received statistics

        // Example: Update average occupancy value
        updateHtmlElement('#avgValue', statistics.avg_occupancy_waiting + '%');
        // Example: Update peak occupancy value
        updateHtmlElement('#peakValue', statistics.peak_occupancy_waiting + '%');

        // Update customs area statistics
        updateHtmlElement('#avgCustomOccupancyValue', statistics.avg_occupancy_custom + '%');
        updateHtmlElement('#peakCustomOccupancyValue', statistics.peak_occupancy_custom + '%');
    }
}

// Function to update an HTML element with a value
function updateHtmlElement(selector, value) {
    // Update the HTML element with the provided value
    $(selector).text(value);
}

// Function to apply date filter
function applyDateFilter() {
    // Get selected start and end dates from date range filter
    var startDate = $('#dateRangeFilter').data('daterangepicker').startDate.format('YYYY-MM-DD');
    var endDate = $('#dateRangeFilter').data('daterangepicker').endDate.format('YYYY-MM-DD');

    // Log selected dates
    console.log('Selected Start Date:', startDate);
    console.log('Selected End Date:', endDate);

    // Fetch and update data based on selected date range
    fetchDataAndUpdate(startDate, endDate);
}


function fetchDataAndUpdate(startDate, endDate) {
    // AJAX request for updating charts
    $.ajax({
        url: '/get_date_range',  // Endpoint for fetching data for the selected date range
        method: 'GET',
        data: { start_date: startDate, end_date: endDate },  // Data containing the selected date range
        success: function (data) {
            // If the AJAX request is successful, update the charts with the received data
            updateCharts(data);
        },
        error: function (error) {
            // If there is an error in the AJAX request, log the error to the console
            console.error('Error applying filter:', error);
        }
    });

    // AJAX request for updating HTML elements with statistics
    $.ajax({
        url: '/get_statistics',  // Endpoint for fetching statistics data
        method: 'GET',
        data: { start_date: startDate, end_date: endDate },  // Data containing the selected date range
        success: function (statistics) {
            // If the AJAX request is successful, update the HTML elements with the received statistics
            updateHtmlElements(statistics);
        },
        error: function (error) {
            // If there is an error in the AJAX request, log the error to the console
            console.error('Error fetching statistics:', error);
        }
    });
}


// Function to periodically update charts
function updateChartsPeriodically() {
    // Call this function once to initialize periodic updates
    setInterval(function() {
        // Get start and end dates from the DateRangePicker
        var startDate = $('#dateRangeFilter').data('daterangepicker').startDate.format('YYYY-MM-DD');
        var endDate = $('#dateRangeFilter').data('daterangepicker').endDate.format('YYYY-MM-DD');

        // AJAX request to update charts with data for the selected date range
        $.ajax({
            url: '/get_date_range',
            method: 'GET',
            data: { start_date: startDate, end_date: endDate },
            success: function (data) {
                // If the AJAX request is successful, update the charts
                updateCharts(data);
            },
            error: function (error) {
                // If there is an error in the AJAX request, log the error to the console
                console.error('Error updating charts:', error);
            }
        });
    }, 5000); // Update every 5 seconds
}

// Initialize periodic chart updates
updateChartsPeriodically();

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
    if (newData && newData.labels && newData.datasets) {
        chart.data.labels = newData.labels;
        chart.data.datasets.forEach((dataset, index) => {
            if (newData.datasets[index] && newData.datasets[index].data) {
                dataset.data = newData.datasets[index].data;
            }
        });
        chart.update();
    } else {
        console.error('Invalid newData object:', newData);
    }
}

// Function to export data to CSV format
function exportData(area) {
    // Get start and end dates from the DateRangePicker
    let dateRange = document.getElementById('dateRangeFilter').value;
    let dates = dateRange.split(' - ');
    let startDate = dates[0];
    let endDate = dates[1];

    // Construct export URL
    let exportUrl = `/export_data_to_csv?start_date=${startDate}&end_date=${endDate}&area=${area}`;
    
    // Redirect to export URL
    window.location.href = exportUrl;
}

// Event listeners for export buttons
document.addEventListener('DOMContentLoaded', function() {
    const exportWaitingAreaBtn = document.getElementById('exportWaitingArea');
    const exportCustomsAreaBtn = document.getElementById('exportCustomsArea');

    // Event listener for waiting area export button
    if (exportWaitingAreaBtn) {
        exportWaitingAreaBtn.addEventListener('click', function() {
            exportData('waiting_area');
        });
    }

    // Event listener for customs area export button
    if (exportCustomsAreaBtn) {
        exportCustomsAreaBtn.addEventListener('click', function() {
            exportData('customs_area');
        });
    }
});
