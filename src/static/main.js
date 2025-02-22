function setupLogging() {
  const updateInveral = 20 * 1000;
  let nextIndex = 0;

  const table = document.getElementById('logs-table');
  const thead = table.querySelector('thead');
  const tbody = table.querySelector('tbody');

  async function fetchLogs() {
    thead.classList.remove('error');
    thead.classList.add('loading');

    try {
      const response = await fetch(`/api/logs/${nextIndex}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error fetching logs:", error);
      thead.classList.add('error');
      return;
    } finally {
      thead.classList.remove('loading');
    }
  }

  function renderLogsTable(newLogs) {
    newLogs.forEach(log => {
      const row = tbody.insertRow(0);
      row.insertCell().textContent = log.now;
      row.insertCell().textContent = log.message;
    });
  }

  async function updateLogs() {
    const newLogs = await fetchLogs();
    if (newLogs && newLogs.logs.length > 0) {
      nextIndex = newLogs.next_index;
      renderLogsTable(newLogs.logs);
    }
  }

  if (table) {
    updateLogs();
    setInterval(updateLogs, updateInveral);
  }
};

document.addEventListener('DOMContentLoaded', function() {
  setupLogging();
});
