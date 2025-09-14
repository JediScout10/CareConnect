// users/static/users/js/dashboard.js

let scoreChart = null;

function getCSRFToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfInput ? csrfInput.value : document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1] || '';
}

document.addEventListener('DOMContentLoaded', function() {
    try {
        initializeDashboard();
    } catch (error) {
        console.error("Initialization error:", error);
        showErrorState("Failed to load dashboard");
    }
});

function initializeDashboard() {
    initializeActionItems();
    initializeChart();
    logActionItems();
}

function logActionItems() {
    const actionItems = document.querySelectorAll('.action-item');
    console.log('Action items found:', actionItems.length);
    actionItems.forEach(item => console.log('Action:', item.dataset.action, 'State:', item.dataset.state, 'Test ID:', item.dataset.testId));
}

function initializeActionItems() {
    // Remove all existing listeners first
    document.querySelectorAll('.action-item[data-listener-attached]').forEach(item => {
        item.removeEventListener('click', handleActionClick);
        item.removeAttribute('data-listener-attached');
    });
    
    // Add new listeners
    document.querySelectorAll('.action-item:not([data-listener-attached])').forEach(item => {
        item.addEventListener('click', () => handleActionClick(item));
        item.setAttribute('data-listener-attached', 'true');
    });
}

function initializeChart() {
    const scoreData = JSON.parse(document.getElementById('scoreData').textContent || '{}');
    if (scoreData?.scores?.length > 0) {
        renderChart(scoreData);
    } else {
        showNoDataMessage();
    }
}

function renderChart(scoreData) {
    const ctx = document.getElementById('scoreChart');
    if (!ctx) return;

    try {
        if (scoreChart) scoreChart.destroy();

        scoreChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: scoreData.dates,
                datasets: [{
                    label: 'Mental Health Score',
                    data: scoreData.scores,
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 20,
                        ticks: {
                            stepSize: 5
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    } catch (error) {
        console.error("Chart rendering error:", error);
    }
}

async function handleActionClick(item) {
    if (item.classList.contains('completed') || item.classList.contains('processing')) {
        return;
    }

    const originalHTML = item.innerHTML;
    showLoadingState(item);

    try {
        const response = await fetch('/users/complete-action/', {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({
                action_text: item.dataset.action,
                state_context: item.dataset.state,
                test_id: item.dataset.testId || null
            })
        });

        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            // Remove the completed action from the list
            item.remove();
            
            // Add to completed tasks
            addCompletedTask(data.completed_action);
            
            showToast('Task completed successfully!', 'success');
        } else {
            throw new Error(data.error || 'Failed to complete task');
        }
    } catch (error) {
        console.error("Error completing task:", error);
        resetActionItem(item, originalHTML);
        showToast(error.message, 'error');
    }
}

function updateActionItems(actions, stateContext, testId) {
    const container = document.querySelector('.action-items-container');
    if (!container) return;
    
    container.innerHTML = '';
    container.dataset.state = stateContext;  // Preserve state context
    container.dataset.testId = testId;      // Preserve test ID
    
    if (actions.length === 0) {
        container.innerHTML = '<p class="text-gray-500">All actions completed!</p>';
        return;
    }

    const fragment = document.createDocumentFragment();
    actions.forEach(actionText => {
        const actionEl = document.createElement('div');
        actionEl.className = 'action-item p-3 mb-2 rounded-lg cursor-pointer hover:bg-gray-50';
        actionEl.dataset.action = actionText;
        actionEl.dataset.state = stateContext;
        actionEl.dataset.testId = testId || '';
        actionEl.innerHTML = `
            <div class="flex items-center">
                <span class="mr-2">📌</span>
                <span>${actionText}</span>
            </div>
        `;
        fragment.appendChild(actionEl);
    });
    
    container.appendChild(fragment);
    
    // Reinitialize event listeners for the new items
    initializeActionItems();
    logActionItems();
}

function addCompletedTask(action) {
    const container = document.querySelector('.completed-tasks-container');
    if (!container) return;

    const taskEl = document.createElement('div');
    taskEl.className = 'completed-task flex justify-between items-center text-sm p-2 bg-gray-50 rounded';
    taskEl.innerHTML = `
        <div class="flex items-center">
            <span class="text-green-500 mr-2">✓</span>
            <span>${action.action_text}</span>
        </div>
        <span class="text-gray-500 text-xs">${action.completed_at}</span>
    `;
    container.prepend(taskEl);
}

function showLoadingState(item) {
    item.innerHTML = `
        <span class="flex items-center">
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Completing...
        </span>
    `;
    item.classList.add('processing');
}

function resetActionItem(item, originalHTML) {
    item.innerHTML = originalHTML;
    item.classList.remove('processing');
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type} animate__animated animate__fadeInUp`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('animate__fadeOutDown');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function showNoDataMessage() {
    const container = document.querySelector('.chart-container');
    if (container) {
        container.innerHTML = `
            <div class="text-center p-4 text-gray-500">
                <p>No test data available yet</p>
                <p class="text-sm">Complete your first mental health test</p>
            </div>
        `;
    }
}

function showErrorState(message) {
    const container = document.querySelector('.chart-container') || document.body;
    container.innerHTML = `
        <div class="error-state p-4 bg-red-50 text-red-700 rounded-lg">
            <p class="font-medium">${message}</p>
            <button onclick="window.location.reload()" class="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm">
                Reload Page
            </button>
        </div>
    `;
}