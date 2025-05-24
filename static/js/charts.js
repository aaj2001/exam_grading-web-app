/**
 * Automated Exam Grading and Cheating Detection
 * Charts and data visualization functions
 */

// The annotation plugin is registered automatically when loaded from CDN

/**
 * Creates a bar chart showing student scores
 * @param {string} elementId - Canvas element ID
 * @param {Array} labels - Array of labels (student names)
 * @param {Array} scores - Array of student scores
 * @param {Array} totals - Array of total possible scores
 */
function createScoreChart(elementId, labels, scores, totals) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Calculate percentages for better visualization
    const percentages = scores.map((score, index) => (score / totals[index]) * 100);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score (%)',
                data: percentages,
                backgroundColor: generateBackgroundColors(percentages),
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            return `Score: ${scores[index]}/${totals[index]} (${percentages[index].toFixed(1)}%)`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Percentage (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Students'
                    }
                }
            }
        }
    });
}

/**
 * Creates a horizontal bar chart
 * @param {string} elementId - Canvas element ID
 * @param {Array} labels - Array of labels
 * @param {Array} values - Array of values
 * @param {string} title - Chart title
 */
function createBarChart(elementId, labels, values, title, threshold) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Convert similarity values to percentages for display
    const percentages = values.map(value => value * 100);
    
    // Convert threshold to percentage if provided
    const thresholdPercentage = threshold ? threshold * 100 : null;
    
    const chartConfig = {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: percentages,
                backgroundColor: generateBackgroundColors(percentages),
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${title}: ${percentages[context.dataIndex].toFixed(1)}%`;
                        }
                    }
                },
                annotation: thresholdPercentage ? {
                    annotations: {
                        thresholdLine: {
                            type: 'line',
                            xMin: thresholdPercentage,
                            xMax: thresholdPercentage,
                            borderColor: 'rgba(255, 0, 0, 0.8)',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            label: {
                                enabled: true,
                                content: `Threshold: ${thresholdPercentage.toFixed(1)}%`,
                                position: 'start'
                            }
                        }
                    }
                } : {}
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Percentage (%)'
                    }
                }
            }
        }
    };
    
    new Chart(ctx, chartConfig);
}

/**
 * Creates a distribution chart (line chart)
 * @param {string} elementId - Canvas element ID
 * @param {Array} labels - Array of labels
 * @param {Array} values - Array of values
 * @param {string} title - Chart title
 */
function createDistributionChart(elementId, labels, values, title) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Convert similarity values to percentages for display
    const percentages = values.map(value => value * 100);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: percentages,
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(75, 192, 192, 1)',
                pointRadius: 5,
                pointHoverRadius: 7,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${title}: ${percentages[context.dataIndex].toFixed(1)}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Percentage (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Students'
                    }
                }
            }
        }
    });
}

/**
 * Generates background colors based on values
 * @param {Array} values - Array of numeric values (percentages)
 * @returns {Array} Array of color strings
 */
function generateBackgroundColors(values) {
    return values.map(value => {
        if (value >= 80) {
            return 'rgba(75, 192, 192, 0.7)'; // Green for high values
        } else if (value >= 60) {
            return 'rgba(54, 162, 235, 0.7)'; // Blue for medium-high values
        } else if (value >= 40) {
            return 'rgba(255, 206, 86, 0.7)'; // Yellow for medium values
        } else {
            return 'rgba(255, 99, 132, 0.7)'; // Red for low values
        }
    });
}

/**
 * Creates a pie chart
 * @param {string} elementId - Canvas element ID
 * @param {Array} labels - Array of labels
 * @param {Array} values - Array of values
 * @param {string} title - Chart title
 */
function createPieChart(elementId, labels, values, title) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: values,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)',
                    'rgba(255, 159, 64, 0.7)',
                    'rgba(199, 199, 199, 0.7)',
                    'rgba(83, 102, 255, 0.7)',
                    'rgba(40, 159, 64, 0.7)',
                    'rgba(210, 99, 132, 0.7)'
                ],
                borderColor: 'rgba(255, 255, 255, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                title: {
                    display: true,
                    text: title
                }
            }
        }
    });
}
