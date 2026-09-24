const api = (u, o) =>
    fetch(u, o).then(async r => {
        let j = await r.json();

        if (!r.ok) {
            throw Error(j.error);
        }

        return j;
    });

async function load() {
    let q = filter.value;

    let [s, e] = await Promise.all([
        api('/api/summary'),
        api('/api/entries' + (q ? '?date=' + q : ''))
    ]);

    let peak = s.hours?.[0]?.hour || '—';

    metrics.innerHTML = `
        <div class="metric">
            <small>Total de entradas</small>
            <strong>${s.total}</strong>
            <small>registros</small>
        </div>

        <div class="metric">
            <small>Perfil mais comum</small>
            <strong>${s.types[0]?.name || '—'}</strong>
            <small>${s.types[0]?.total || 0}</small>
        </div>

        <div class="metric">
            <small>Setor mais movimentado</small>
            <strong>${s.sectors[0]?.name || '—'}</strong>
            <small>${s.sectors[0]?.total || 0}</small>
        </div>

        <div class="metric">
            <small>Horário de pico</small>
            <strong>${peak}h</strong>
            <small>maior concentração</small>
        </div>
    `;

    let mx = Math.max(
        ...s.months.map(x => x.total),
        1
    );

    months.innerHTML = s.months.map(x => `
        <div class="month">
            <div
                class="bar"
                style="height:${Math.max(x.total / mx * 90, 3)}%"
            ></div>

            <small>${x.month.slice(5)}</small>
        </div>
    `).join('');

    let mt = Math.max(
        ...s.types.map(x => x.total),
        1
    );

    types.innerHTML = s.types.map(x => `
        <div class="type">
            <div>
                ${x.name}
                <b>${x.total}</b>
            </div>

            <div class="track">
                <i style="width:${x.total / mt * 100}%"></i>
            </div>
        </div>
    `).join('');

    rows.innerHTML = e.map(x => `
        <tr>
            <td>${x.name}</td>
            <td>${x.type}</td>
            <td>${x.age_group}</td>
            <td>${x.sex}</td>
            <td>${x.sector}</td>
            <td>${x.date} ${x.entry_time}</td>
            <td>${x.exit_time || '—'}</td>

            <td>
                <button onclick="del(${x.id})">
                    Excluir
                </button>
            </td>
        </tr>
    `).join('');
}

function openForm() {
    modal.className = 'show';

    date.value = new Date()
        .toISOString()
        .slice(0, 10);

    entry.value = new Date()
        .toTimeString()
        .slice(0, 5);
}

function closeForm() {
    modal.className = '';
}

async function save(e) {
    e.preventDefault();

    await api('/api/entries', {
        method: 'POST',

        headers: {
            'Content-Type': 'application/json'
        },

        body: JSON.stringify({
            name: name.value,
            type: type.value,
            age_group: age.value,
            sex: sex.value,
            sector: sector.value,
            date: date.value,
            entry_time: entry.value,
            exit_time: exit.value
        })
    });

    closeForm();
    e.target.reset();
    load();
}

async function del(id) {
    if (confirm('Excluir registro?')) {
        await api('/api/entries/' + id, {
            method: 'DELETE'
        });

        load();
    }
}

load();