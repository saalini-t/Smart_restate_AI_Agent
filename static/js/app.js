document.addEventListener('DOMContentLoaded', function() {
    // Activate Bootstrap components
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // Add smooth scrolling for all hash links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
                
                // Update active nav item
                document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
                    link.classList.remove('active');
                });
                this.classList.add('active');
            }
        });
    });

    // Highlight the active nav item on scroll
    window.addEventListener('scroll', function() {
        const sections = document.querySelectorAll('section');
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        
        let currentSection = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            
            if (pageYOffset >= sectionTop - 200) {
                currentSection = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${currentSection}`) {
                link.classList.add('active');
            }
        });
    });

    // Initialize charts
    initializeCharts();

    // Form submission handlers
    initializeFormHandlers();

    // Add animation classes to elements when they come into view
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fadeIn');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    animatedElements.forEach(el => {
        observer.observe(el);
    });
});

function initializeCharts() {
    // Chart.js global settings
    Chart.defaults.color = '#adb5bd';
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.plugins.legend.position = 'top';
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(33, 37, 41, 0.9)';
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.tooltip.titleFont = { weight: 'bold' };
    
    // Economic Trends Charts
    if (document.getElementById('economic-trends-chart')) {
        const ctx = document.getElementById('economic-trends-chart').getContext('2d');
        const economicTrendsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
                datasets: [
                    {
                        label: 'Interest Rate (%)',
                        data: [5.25, 5.25, 5.00, 5.00, 4.75, 4.75, 4.75, 4.50, 4.50, 4.50, 4.25, 4.25],
                        borderColor: '#3a8dff',
                        backgroundColor: 'rgba(58, 141, 255, 0.1)',
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Inflation Rate (%)',
                        data: [3.1, 3.0, 2.9, 2.8, 2.7, 2.8, 2.9, 3.0, 3.1, 3.0, 2.9, 2.8],
                        borderColor: '#ff9a9e',
                        backgroundColor: 'rgba(255, 154, 158, 0.1)',
                        tension: 0.3,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    if (document.getElementById('housing-market-chart')) {
        const ctx = document.getElementById('housing-market-chart').getContext('2d');
        const housingMarketChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
                datasets: [
                    {
                        label: 'Home Sales (000s)',
                        data: [617, 610, 605, 598, 602, 609, 615, 608, 600, 595, 590, 585],
                        borderColor: '#84fab0',
                        backgroundColor: 'rgba(132, 250, 176, 0.1)',
                        tension: 0.3,
                        fill: true,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Housing Index',
                        data: [100, 99.5, 99.2, 98.9, 98.1, 97.6, 97.1, 97.8, 98.2, 97.9, 97.5, 97.2],
                        borderColor: '#f6d365',
                        backgroundColor: 'rgba(246, 211, 101, 0.1)',
                        tension: 0.3,
                        fill: true,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        },
                        min: 95,
                        max: 105
                    }
                }
            }
        });
    }

    // Property Price Forecast Chart
    if (document.getElementById('price-forecast-chart')) {
        const ctx = document.getElementById('price-forecast-chart').getContext('2d');
        const priceForecastChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
                datasets: [{
                    label: 'Predicted Price',
                    data: [2425500, 2432903, 2450883, 2449548, 2458437, 2467622, 2465436, 2466684, 2478888, 2475670, 2493942, 2509071],
                    borderColor: '#3a8dff',
                    backgroundColor: 'rgba(58, 141, 255, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Price: $' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + (value / 1000000).toFixed(1) + 'M';
                            }
                        }
                    }
                }
            }
        });
    }

    // Location Score Chart (Radar)
    if (document.getElementById('location-score-chart')) {
        const ctx = document.getElementById('location-score-chart').getContext('2d');
        const locationScoreChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Schools', 'Healthcare', 'Transport', 'Crime', 'Green Zones', 'Development'],
                datasets: [{
                    label: 'Location Score',
                    data: [77, 71, 74, 74, 63, 74],
                    borderColor: '#3a8dff',
                    backgroundColor: 'rgba(58, 141, 255, 0.2)',
                    pointBackgroundColor: '#3a8dff',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#3a8dff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                elements: {
                    line: {
                        borderWidth: 2
                    }
                },
                scales: {
                    r: {
                        angleLines: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        pointLabels: {
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        },
                        suggestedMin: 0,
                        suggestedMax: 100,
                        ticks: {
                            stepSize: 20,
                            backdropColor: 'transparent'
                        }
                    }
                }
            }
        });
    }

    // Price Momentum Chart
    if (document.getElementById('price-momentum-chart')) {
        const ctx = document.getElementById('price-momentum-chart').getContext('2d');
        const priceMomentumChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
                datasets: [{
                    label: 'Price Momentum',
                    data: [0.5, 0.8, 1.2, 1.4, 1.1, 0.9, 0.7, 0.5, 0.3, 0.2, 0.4, 0.7],
                    borderColor: '#84fab0',
                    backgroundColor: 'rgba(132, 250, 176, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Momentum: ' + context.parsed.y.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        suggestedMin: -1,
                        suggestedMax: 2
                    }
                }
            }
        });
    }

    // ROI Drivers Chart (Doughnut)
    if (document.getElementById('roi-drivers-chart')) {
        const ctx = document.getElementById('roi-drivers-chart').getContext('2d');
        const roiDriversChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Rental Income', 'Appreciation'],
                datasets: [{
                    label: 'ROI Drivers',
                    data: [420000, 492719],
                    backgroundColor: [
                        '#3a8dff',
                        '#84fab0'
                    ],
                    borderColor: [
                        '#3a8dff',
                        '#84fab0'
                    ],
                    borderWidth: 1,
                    hoverOffset: 15
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true, // Set to true to control size
                aspectRatio: 2, // Wider than tall
                cutout: '70%',
                layout: {
                    padding: {
                        top: 10,
                        bottom: 10,
                        left: 10,
                        right: 120 // Make room for legend
                    }
                },
                plugins: {
                    legend: {
                        position: 'right',
                        align: 'center',
                        labels: {
                            boxWidth: 15,
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 15,
                            font: {
                                size: 11
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: $${value.toLocaleString()} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
}

function initializeFormHandlers() {
    // Make sure all form initialization happens only once by using a flag
    if (window.formsInitialized) return;
    window.formsInitialized = true;
    
    console.log("Initializing form handlers...");
    
    // Property Price Prediction Form
    const pricePredictionForm = document.getElementById('price-prediction-form');
    if (pricePredictionForm) {
        pricePredictionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            submitButton.disabled = true;
            
            // Collect form data
            const formData = {
                location: document.getElementById('location').value,
                property_type: document.getElementById('property-type').value,
                area_sqft: parseInt(document.getElementById('area-sqft').value),
                bedrooms: parseInt(document.getElementById('bedrooms').value || 0),
                bathrooms: parseInt(document.getElementById('bathrooms').value || 0),
                year_built: parseInt(document.getElementById('year-built').value || 0),
                forecast_period: document.getElementById('forecast-period').value
            };
            
            // Send API request
            fetch('/api/property-price/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Show results
                    document.getElementById('prediction-results').classList.remove('d-none');
                    document.getElementById('current-price').textContent = '$' + data.data.current_price.toLocaleString();
                    document.getElementById('price-per-sqft').textContent = '$' + data.data.price_per_sqft.toLocaleString() + ' per sqft';
                    
                    const marketAssessment = document.getElementById('market-assessment');
                    const assessmentPercentage = document.getElementById('assessment-percentage');
                    
                    marketAssessment.textContent = data.data.market_assessment.assessment.charAt(0).toUpperCase() + data.data.market_assessment.assessment.slice(1);
                    
                    if (data.data.market_assessment.assessment === 'overvalued') {
                        marketAssessment.className = 'fs-2 fw-bold text-danger';
                        assessmentPercentage.textContent = data.data.market_assessment.percentage + '% above fair market value';
                    } else if (data.data.market_assessment.assessment === 'undervalued') {
                        marketAssessment.className = 'fs-2 fw-bold text-success';
                        assessmentPercentage.textContent = data.data.market_assessment.percentage + '% below fair market value';
                    } else {
                        marketAssessment.className = 'fs-2 fw-bold text-warning';
                        assessmentPercentage.textContent = 'Within ' + data.data.market_assessment.percentage + '% of fair market value';
                    }
                    
                    // Update forecast chart
                    updatePriceForecastChart(data.data.forecast);
                    
                    // Scroll to results
                    document.getElementById('prediction-results').scrollIntoView({ behavior: 'smooth', block: 'start' });
                } else {
                    alert('Error: ' + (data.message || 'Failed to predict property price'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error fetching data. Please try again.');
            })
            .finally(() => {
                // Reset button state
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            });
        });
        console.log("Price prediction form handler initialized");
    }

    // Location Score Form
    const locationScoreForm = document.getElementById('location-score-form');
    if (locationScoreForm) {
        locationScoreForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            submitButton.disabled = true;
            
            // Collect form data
            const location = document.getElementById('location-address').value;
            const radius = document.getElementById('location-radius').value;
            
            // Send API request
            fetch(`/api/location-intelligence/score?location=${encodeURIComponent(location)}&radius=${radius}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Show results
                    document.getElementById('location-results').classList.remove('d-none');
                    
                    // Update scores
                    document.getElementById('total-score').textContent = data.data.total_score + '/100';
                    document.getElementById('total-score-bar').style.width = data.data.total_score + '%';
                    document.getElementById('total-score-bar').setAttribute('aria-valuenow', data.data.total_score);
                    
                    document.getElementById('schools-score').textContent = data.data.schools_score + '/100';
                    document.getElementById('schools-score-bar').style.width = data.data.schools_score + '%';
                    document.getElementById('schools-score-bar').setAttribute('aria-valuenow', data.data.schools_score);
                    
                    document.getElementById('hospitals-score').textContent = data.data.hospitals_score + '/100';
                    document.getElementById('hospitals-score-bar').style.width = data.data.hospitals_score + '%';
                    document.getElementById('hospitals-score-bar').setAttribute('aria-valuenow', data.data.hospitals_score);
                    
                    document.getElementById('transport-score').textContent = data.data.transport_score + '/100';
                    document.getElementById('transport-score-bar').style.width = data.data.transport_score + '%';
                    document.getElementById('transport-score-bar').setAttribute('aria-valuenow', data.data.transport_score);
                    
                    document.getElementById('crime-score').textContent = data.data.crime_score + '/100';
                    document.getElementById('crime-score-bar').style.width = data.data.crime_score + '%';
                    document.getElementById('crime-score-bar').setAttribute('aria-valuenow', data.data.crime_score);
                    
                    document.getElementById('green-zones-score').textContent = data.data.green_zones_score + '/100';
                    document.getElementById('green-zones-score-bar').style.width = data.data.green_zones_score + '%';
                    document.getElementById('green-zones-score-bar').setAttribute('aria-valuenow', data.data.green_zones_score);
                    
                    document.getElementById('development-score').textContent = data.data.development_score + '/100';
                    document.getElementById('development-score-bar').style.width = data.data.development_score + '%';
                    document.getElementById('development-score-bar').setAttribute('aria-valuenow', data.data.development_score);
                    
                    // Update radar chart
                    updateLocationScoreChart([
                        data.data.schools_score,
                        data.data.hospitals_score,
                        data.data.transport_score,
                        data.data.crime_score,
                        data.data.green_zones_score,
                        data.data.development_score
                    ]);
                    
                    // Scroll to results
                    document.getElementById('location-results').scrollIntoView({ behavior: 'smooth', block: 'start' });
                } else {
                    alert('Error: ' + (data.message || 'Failed to fetch location score'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error fetching data. Please try again.');
            })
            .finally(() => {
                // Reset button state
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            });
        });
        console.log("Location score form handler initialized");
    }

    // Investment Recommendation Form
    const investmentRecommendationForm = document.getElementById('investment-recommendation-form');
    if (investmentRecommendationForm) {
        investmentRecommendationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            submitButton.disabled = true;
            
            // Collect form data
            const formData = {
                location: document.getElementById('investment-location').value,
                property_type: document.getElementById('investment-property-type').value,
                investment_goal: document.getElementById('investment-goal').value,
                timeframe: parseInt(document.getElementById('timeframe').value),
                budget: parseInt(document.getElementById('budget').value || 0)
            };
            
            // Send API request
            fetch('/api/investment-timing/recommendation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Show results
                    document.getElementById('investment-results').classList.remove('d-none');
                    
                    // Do something with the data
                    document.getElementById('investment-results').scrollIntoView({ behavior: 'smooth', block: 'start' });
                } else {
                    alert('Error: ' + (data.message || 'Failed to get investment recommendation'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error fetching data. Please try again.');
            })
            .finally(() => {
                // Reset button state
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            });
        });
        console.log("Investment recommendation form handler initialized");
    }

    // ROI Calculator Form (with once-only initialization)
    const roiCalculatorForm = document.getElementById('roi-calculator-form');
    if (roiCalculatorForm && !roiCalculatorForm.hasAttribute('data-initialized')) {
        roiCalculatorForm.setAttribute('data-initialized', 'true');
        
        roiCalculatorForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state
            const submitButton = this.querySelector('button[type="submit"]');
            if (!submitButton) return;
            
            const originalText = submitButton.textContent;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            submitButton.disabled = true;
            
            // Collect form data
            const formData = {
                location: document.getElementById('roi-location').value,
                property_type: document.getElementById('roi-property-type').value,
                purchase_price: parseInt(document.getElementById('purchase-price').value),
                investment_goal: document.getElementById('roi-investment-goal').value,
                timeframe: parseInt(document.getElementById('roi-timeframe').value),
                additional_investment: parseInt(document.getElementById('additional-investment').value || 0),
                expected_rent: parseInt(document.getElementById('expected-rent').value || 0),
                expected_expenses: parseInt(document.getElementById('expected-expenses').value || 0)
            };
            
            // Send API request
            fetch('/api/roi-calculator/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Show results
                    const resultsDiv = document.getElementById('roi-results');
                    if (resultsDiv) {
                        resultsDiv.classList.remove('d-none');
                        
                        // Update the results display
                        document.getElementById('total-roi').textContent = data.data.roi_percentage.toFixed(2) + '%';
                        document.getElementById('annual-roi').textContent = data.data.annual_roi.toFixed(2) + '% annually over ' + data.data.timeframe_years + ' years';
                        
                        document.getElementById('monthly-cash-flow').textContent = '$' + data.data.monthly_cash_flow.toLocaleString();
                        document.getElementById('annual-cash-flow').textContent = '$' + data.data.annual_cash_flow.toLocaleString() + ' annually';
                        
                        const breakeven = data.data.breakeven_months / 12;
                        document.getElementById('breakeven-time').textContent = breakeven.toFixed(1) + ' years';
                        
                        document.getElementById('cap-rate').textContent = data.data.cap_rate.toFixed(2) + '%';
                        document.getElementById('cash-on-cash').textContent = data.data.cash_on_cash_return.toFixed(2) + '%';
                        
                        // Update ROI drivers chart
                        updateRoiDriversChart({
                            rental: data.data.return_drivers.rental_income,
                            appreciation: data.data.return_drivers.appreciation
                        });
                        
                        // Scroll to results
                        resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                } else {
                    alert('Error: ' + (data.message || 'Failed to calculate ROI'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error fetching data. Please try again.');
            })
            .finally(() => {
                // Reset button state
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            });
        });
        console.log("ROI calculator form handler initialized");
    }
}

// Chart update functions
function updatePriceForecastChart(forecastData) {
    const chart = Chart.getChart('price-forecast-chart');
    if (chart) {
        const labels = forecastData.map(item => item.date.substring(0, 7));
        const prices = forecastData.map(item => item.price);
        
        chart.data.labels = labels;
        chart.data.datasets[0].data = prices;
        chart.update();
    }
}

function updateLocationScoreChart(scoreData) {
    const chart = Chart.getChart('location-score-chart');
    if (chart) {
        chart.data.datasets[0].data = scoreData;
        chart.update();
    }
}

function updateRoiDriversChart(driverData) {
    const chart = Chart.getChart('roi-drivers-chart');
    if (chart) {
        chart.data.datasets[0].data = [driverData.rental, driverData.appreciation];
        chart.update();
    }
}

// Export Dashboard PDF
document.addEventListener('DOMContentLoaded', function() {
    const exportReportBtn = document.getElementById('export-report-btn');
    if (exportReportBtn) {
        exportReportBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
            
            const userData = {
                user_id: 'user123',
                location: document.getElementById('location')?.value || 'San Francisco, CA',
                include_economic_data: true,
                include_property_data: true,
                include_predictions: true,
                timeframe: '1y'
            };
            
            fetch('/api/dashboard/export-pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            })
            .then(response => {
                if (response.ok) {
                    return response.blob();
                }
                throw new Error('Network response was not ok.');
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'smart_estate_report.pdf';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                
                this.disabled = false;
                this.textContent = 'Export PDF Report';
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error generating PDF. Please try again.');
                
                this.disabled = false;
                this.textContent = 'Export PDF Report';
            });
        });
    }
});