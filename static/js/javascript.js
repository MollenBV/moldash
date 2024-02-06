// Function to initialize charts
function initializeChart(chartId, chartData) {
    var ctx = document.getElementById(chartId).getContext('2d');
    var chartType = chartId === 'waitingAreaChart' ? 'bar' : 'line';
    
    // Extract the line dataset separately
    var lineDataset = chartData.datasets.find(dataset => dataset.label === 'Entrance Point Count (Customs Area)');

    // Remove the line dataset temporarily
    var datasetsWithoutLine = chartData.datasets.filter(dataset => dataset.label !== 'Entrance Point Count (Customs Area)');

    var chart = new Chart(ctx, {
        type: chartType,
        data: {
            labels: chartData.labels,
            datasets: datasetsWithoutLine.map(dataset => ({
                label: dataset.label,
                data: dataset.data,
                borderColor: dataset.borderColor,
                borderWidth: dataset.borderWidth,
                backgroundColor: dataset.backgroundColor,
                fill: dataset.fill,
                hidden: dataset.label === 'Total Seats (Waiting Area)' || dataset.label === 'Total People (Waiting Area)'
            })),
        },
        options: {
            plugins: {
                title: {
                    display: true,
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

    // Add the line dataset back to the chart
    if (chartType === 'line' && lineDataset) {
        chart.data.datasets.push(lineDataset);
    }

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

        // Update customs area statistics
        updateHtmlElement('#avgCustomOccupancyValue', statistics.avg_occupancy_custom + '%');
        updateHtmlElement('#peakCustomOccupancyValue', statistics.peak_occupancy_custom + '%');
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

    fetchDataAndUpdate(startDate, endDate);
}

function fetchDataAndUpdate(startDate, endDate) {
    // AJAX request for updating charts
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

    // AJAX request for updating HTML elements
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

function updateChartsPeriodically() {
    // Call this function once to initialize periodic updates
    setInterval(function() {
        var startDate = $('#dateRangeFilter').data('daterangepicker').startDate.format('YYYY-MM-DD');
        var endDate = $('#dateRangeFilter').data('daterangepicker').endDate.format('YYYY-MM-DD');

        // AJAX request just for updating charts, reusing the current date range
        $.ajax({
            url: '/get_date_range',
            method: 'GET',
            data: { start_date: startDate, end_date: endDate },
            success: function (data) {
                updateCharts(data);
            },
            error: function (error) {
                console.error('Error updating charts:', error);
            }
        });
    }, 5000); // Update every 5 seconds
}

// Initialize the periodic chart updates
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


function exportData(area) {
    let dateRange = document.getElementById('dateRangeFilter').value;
    let dates = dateRange.split(' - ');
    let startDate = dates[0];
    let endDate = dates[1];

    let exportUrl = `/export_data_to_csv?start_date=${startDate}&end_date=${endDate}&area=${area}`;
    window.location.href = exportUrl;
}

// Event listeners for the export buttons
document.addEventListener('DOMContentLoaded', function() {
    const exportWaitingAreaBtn = document.getElementById('exportWaitingArea');
    const exportCustomsAreaBtn = document.getElementById('exportCustomsArea');

    if (exportWaitingAreaBtn) {
        exportWaitingAreaBtn.addEventListener('click', function() {
            exportData('waiting_area');
        });
    }

    if (exportCustomsAreaBtn) {
        exportCustomsAreaBtn.addEventListener('click', function() {
            exportData('customs_area');
        });
    }
});