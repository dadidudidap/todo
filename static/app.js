const state = { status: 'all', tasks: [], page: 1, perPage: 10 };

// Find one page element using a CSS selector.
const $ = (selector) => document.querySelector(selector);

const progressRingStyles = document.createElement('style');
progressRingStyles.textContent = `
  .progress-ring {
    --progress: 0%;
    position: relative;
    width: 72px;
    height: 72px;
    border: none;
    border-top-color: transparent;
    border-right-color: transparent;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: conic-gradient(from 0deg, var(--lime) var(--progress), var(--line) 0);
    overflow: visible;
    padding: 0;
    transform: none !important;
  }

  .progress-ring::before {
    content: "";
    position: absolute;
    inset: 7px;
    border-radius: 50%;
    background: var(--paper);
    z-index: 1;
  }

  .progress-text {
    position: relative;
    z-index: 3;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    line-height: 1;
    width: 100%;
    height: 100%;
    gap: 0;
    margin: 0;
    padding: 0;
  }

  .progress-text span,
  .progress-text small {
    display: block;
    line-height: 1;
    text-align: center;
    margin: 0;
    padding: 0;
    transform: none;
  }

  .progress-text small {
    letter-spacing: 0.08em;
    text-transform: lowercase;
    font-size: 8px;
    opacity: 0.85;
  }
`;
document.head.appendChild(progressRingStyles);

const themeToggle = $('#theme-toggle');

if (localStorage.getItem('todo-theme') !== 'light') {
  document.body.dataset.theme = 'dark';
} else {
  document.body.dataset.theme = 'light';
}

themeToggle.textContent = document.body.dataset.theme === 'dark'
  ? 'Light mode'
  : 'Dark mode';
// Toggle dark mode and remember the user's preference.
themeToggle.addEventListener('click', () => {
  const darkMode = document.body.dataset.theme !== 'dark';
  document.body.dataset.theme = darkMode ? 'dark' : 'light';
  localStorage.setItem('todo-theme', darkMode ? 'dark' : 'light');
  themeToggle.textContent = darkMode ? 'Light mode' : 'Dark mode';
});

function formatDate(value) {
  // Turn an ISO date into the short date shown under each task.
  if (!value) return 'No due date';
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(new Date(`${value}T00:00:00`));
}

function getDueDateClass(dueDate, complete) {
  if (!dueDate) return '';
  const days = (new Date(dueDate) - new Date()) / (1000 * 60 * 60 * 24);
  if (!complete) {
    if (days < 3) return 'due-close';
    if (days < 7) return 'due-close-enough';
  }
  return '';
}

async function api(path, options = {}) {
  // Send a request to the Flask API and convert its response to JSON.
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!response.ok) {
    throw new Error((await response.json()).error || 'Something went wrong.');
  }

  return response.status === 204 ? null : response.json();
}

function render() {
  // Rebuild the visible task list and update counts and progress.
  const list = $('#task-list');
  const visible = state.tasks.filter((task) => (
    state.status === 'all'
    || (state.status === 'active' && !task.completed)
    || (state.status === 'completed' && task.completed)
  ));

  const totalPages = Math.max(1, Math.ceil(visible.length / state.perPage));
  if (state.page > totalPages) state.page = totalPages;
  const start = (state.page - 1) * state.perPage;
  const paged = visible.slice(start, start + state.perPage);

  list.innerHTML = paged.map((task, index) => `
    <article class="task ${task.completed ? 'completed' : ''}" style="animation-delay:${index * 35}ms">
      <button class="task-check" data-action="complete" data-id="${task.id}" aria-label="Mark ${task.title} complete"></button>
      <div>
        <div class="task-title">${escapeHtml(task.title)}</div>
        <div class="task-meta ${getDueDateClass(task.due_date, task.completed)}">${task.completed ? 'Complete on ' + formatDate(task.complete_date) : formatDate(task.due_date)}</div>
      </div>
      <span class="priority priority-${task.priority}">${task.priority}</span>
      <button class="delete" data-action="delete" data-id="${task.id}" aria-label="Delete ${task.title}">×</button>
    </article>
  `).join('');

  const pagination = $('#pagination');
  if (totalPages <= 1) {
    pagination.innerHTML = '';
  } else {
    let buttons = '';
    buttons += `<button class="page-btn" data-page="prev" ${state.page === 1 ? 'disabled' : ''}>‹</button>`;
    for (let i = 1; i <= totalPages; i++) {
      buttons += `<button class="page-btn ${i === state.page ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }
    buttons += `<button class="page-btn" data-page="next" ${state.page === totalPages ? 'disabled' : ''}>›</button>`;
    pagination.innerHTML = buttons;
  }

  $('#empty-state').hidden = visible.length > 0;
  $('#all-count').textContent = state.tasks.length;
  $('#active-count').textContent = state.tasks.filter((task) => !task.completed).length;
  $('#completed-count').textContent = state.tasks.filter((task) => task.completed).length;
  const done = state.tasks.length
    ? Math.round(state.tasks.filter((task) => task.completed).length / state.tasks.length * 100)
    : 0;
  const progressRing = $('#progress-ring');
  progressRing.style.setProperty('--progress', `${done}%`);
  progressRing.setAttribute('aria-valuenow', String(done));
  $('#progress-percent').textContent = `${done}%`;
  $('#list-label').textContent = `${state.status.toUpperCase()} TASKS`;
}

function escapeHtml(value) {
  // Escape user-entered text before inserting it into HTML.
  const entities = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#039;',
    '"': '&quot;',
  };

  return value.replace(/[&<>'"]/g, (char) => entities[char]);
}

async function loadTasks() {
  // Load all tasks, apply the browser-side order, and render them.
  state.tasks = (await api('/api/tasks?status=all'));
  render();
}

// Validate the form and create a new task through the API.
$('#add-task').addEventListener('click', async () => {
  const input = $('#task-input');

  if (!input.value.trim()) {
    input.focus();
    return;
  }

  try {
    await api('/api/tasks', {
      method: 'POST',
      body: JSON.stringify({
        title: input.value,
        priority: $('#priority-input').value,
        due_date: $('#date-input').value,
      }),
    });
    input.value = '';
    $('#date-input').value = '';
    await loadTasks();
  } catch (error) {
    alert(error.message);
  }
});

// Allow Enter to submit the task form without clicking the add button.
$('#task-input').addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    $('#add-task').click();
  }
});

// Switch the active task filter and redraw the visible list.
document.querySelectorAll('.filter').forEach((button) => button.addEventListener('click', () => {
  document.querySelectorAll('.filter').forEach((item) => item.classList.remove('active'));
  button.classList.add('active');
  state.status = button.dataset.status;
  state.page = 1;
  render();
}));

// Complete a task or arm it for deletion when one of its action buttons is clicked.
$('#task-list').addEventListener('click', async (event) => {
  const button = event.target.closest('[data-action]');
  if (!button) return;
  const task = state.tasks.find((item) => item.id === Number(button.dataset.id));
  if (!task) return;

  try {
    if (button.dataset.action === 'complete') {
      await api(`/api/tasks/${task.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ 
          complete_date: !task.completed ? new Date().toISOString().split('T')[0] : null,
          completed: !task.completed,
        }),
      });
    }

    if (button.dataset.action === 'delete') {
      if (!button.dataset.deleteReady) {
        button.dataset.deleteReady = 'true';
        button.classList.add('delete-ready');
        button.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v5M14 11v5"/></svg>';
        button.title = 'Click again to delete';
        return;
      }
      await api(`/api/tasks/${task.id}`, { method: 'DELETE' });
    }
    await loadTasks();
  } catch (error) {
    alert(error.message);
  }
});

// Remove all completed tasks and refresh the list.
$('#clear-completed').addEventListener('click', async () => {
  await api('/api/tasks', { method: 'DELETE' });
  await loadTasks();
});

// Handle pagination button clicks.
$('#pagination').addEventListener('click', (event) => {
  const button = event.target.closest('.page-btn');
  if (!button || button.disabled) return;
  const val = button.dataset.page;
  if (val === 'prev') state.page--;
  else if (val === 'next') state.page++;
  else state.page = Number(val);
  render();
});

$('#today-label').textContent = new Intl.DateTimeFormat('en', {
  weekday: 'long',
  month: 'long',
  day: 'numeric',
}).format(new Date());

loadTasks().catch((error) => alert(error.message));
