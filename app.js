const api = (u, o) =>
    fetch(u, o).then(async r => {
        let j = await r.json();

        if (!r.ok) {
            throw Error(j.error);
        }

        return j;
    });

let mode;
let id = null;

async function load() {
    let [s, p, t] = await Promise.all([
        api('/api/summary'),
        api('/api/projects'),
        api('/api/tasks')
    ]);

    let ps = Object.fromEntries(
        s.projects.map(x => [x.status, x.total])
    );

    let ts = Object.fromEntries(
        s.tasks.map(x => [x.status, x.total])
    );

    stats.innerHTML = `
        <div class="stat">
            <small>Projetos ativos</small>
            <strong>
                ${(ps['A fazer'] || 0) + (ps['Em andamento'] || 0)}
            </strong>
        </div>

        <div class="stat">
            <small>Concluídos</small>
            <strong>${ps['Concluído'] || 0}</strong>
        </div>

        <div class="stat">
            <small>Tarefas pendentes</small>
            <strong>
                ${(ts['A fazer'] || 0) + (ts['Em andamento'] || 0)}
            </strong>
        </div>

        <div class="stat">
            <small>Tarefas concluídas</small>
            <strong>${ts['Concluído'] || 0}</strong>
        </div>
    `;

    count.textContent = `(${p.length})`;

    projects.innerHTML = p.map(x => `
        <div class="project">
            <h3>${x.name}</h3>

            <p>${x.description}</p>

            <span class="pill">${x.status}</span>

            <div style="margin-top:14px;color:#7b7589;font-size:11px">
                ${x.priority} · ${x.due_date || 'sem prazo'}
            </div>

            <div class="actions">
                <button onclick="editProject(${x.id})">
                    Editar
                </button>

                <button onclick="delProject(${x.id})">
                    Excluir
                </button>
            </div>
        </div>
    `).join('');

    tasks.innerHTML = t.map(x => `
        <tr>
            <td>${x.title}</td>
            <td>${x.project_name}</td>
            <td>${x.responsible}</td>
            <td>${x.due_date || '—'}</td>
            <td>${x.priority}</td>

            <td>
                <span class="status ${x.status === 'Concluído' ? 'done' : ''}">
                    ${x.status}
                </span>
            </td>

            <td>
                <button class="link" onclick="editTask(${x.id})">
                    Editar
                </button>

                <button class="link" onclick="delTask(${x.id})">
                    Excluir
                </button>
            </td>
        </tr>
    `).join('');
}

function projectFields(x = {}) {
    return `
        <input
            id="name"
            placeholder="Nome"
            value="${x.name || ''}"
            required
        >

        <input
            id="desc"
            placeholder="Descrição"
            value="${x.description || ''}"
        >

        <select id="status">
            ${['A fazer', 'Em andamento', 'Concluído']
                .map(v => `
                    <option ${x.status === v ? 'selected' : ''}>
                        ${v}
                    </option>
                `)
                .join('')}
        </select>

        <select id="priority">
            ${['Baixa', 'Média', 'Alta']
                .map(v => `
                    <option ${x.priority === v ? 'selected' : ''}>
                        ${v}
                    </option>
                `)
                .join('')}
        </select>

        <input
            id="due"
            type="date"
            value="${x.due_date || ''}"
        >
    `;
}

function taskFields(ps, x = {}) {
    return `
        <input
            id="task"
            placeholder="Tarefa"
            value="${x.title || ''}"
            required
        >

        <select id="project">
            ${ps.map(v => `
                <option
                    value="${v.id}"
                    ${x.project_id == v.id ? 'selected' : ''}
                >
                    ${v.name}
                </option>
            `).join('')}
        </select>

        <input
            id="resp"
            placeholder="Responsável"
            value="${x.responsible || ''}"
        >

        <input
            id="due"
            type="date"
            value="${x.due_date || ''}"
        >

        <select id="priority">
            ${['Baixa', 'Média', 'Alta']
                .map(v => `
                    <option ${x.priority === v ? 'selected' : ''}>
                        ${v}
                    </option>
                `)
                .join('')}
        </select>

        <select id="status">
            ${['A fazer', 'Em andamento', 'Concluído']
                .map(v => `
                    <option ${x.status === v ? 'selected' : ''}>
                        ${v}
                    </option>
                `)
                .join('')}
        </select>
    `;
}

function open(t, f) {
    title.textContent = t;
    fields.innerHTML = f;
    modal.className = 'show';
}

function closeForm() {
    modal.className = '';
    id = null;
}

async function newProject() {
    mode = 'project';
    open('Novo projeto', projectFields());
}

async function newTask() {
    let p = await api('/api/projects');

    if (!p.length) {
        return alert('Crie um projeto primeiro');
    }

    mode = 'task';
    open('Nova tarefa', taskFields(p));
}

async function editProject(i) {
    let p = await api('/api/projects');

    id = i;
    mode = 'project';

    open(
        'Editar projeto',
        projectFields(p.find(x => x.id === i))
    );
}

async function editTask(i) {
    let [p, t] = await Promise.all([
        api('/api/projects'),
        api('/api/tasks')
    ]);

    id = i;
    mode = 'task';

    open(
        'Editar tarefa',
        taskFields(p, t.find(x => x.id === i))
    );
}

async function save(e) {
    e.preventDefault();

    let d = mode === 'project'
        ? {
            name: name.value,
            description: desc.value,
            status: status.value,
            priority: priority.value,
            due_date: due.value
        }
        : {
            title: task.value,
            project_id: project.value,
            responsible: resp.value,
            due_date: due.value,
            priority: priority.value,
            status: status.value
        };

    await api(
        '/api/' +
        (mode === 'project' ? 'projects' : 'tasks') +
        (id ? '/' + id : ''),
        {
            method: id ? 'PUT' : 'POST',

            headers: {
                'Content-Type': 'application/json'
            },

            body: JSON.stringify(d)
        }
    );

    closeForm();
    load();
}

async function delProject(i) {
    if (confirm('Excluir projeto?')) {
        await api('/api/projects/' + i, {
            method: 'DELETE'
        });

        load();
    }
}

async function delTask(i) {
    if (confirm('Excluir tarefa?')) {
        await api('/api/tasks/' + i, {
            method: 'DELETE'
        });

        load();
    }
}

load();