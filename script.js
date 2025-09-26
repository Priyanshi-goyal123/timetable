// Only the timetable/subjects helper (no auth here).
// It keeps the "subjects" input updated and renders a small list of added subjects.

let subjects = [];

function parseSubjectsInput() {
    const input = document.getElementById('subjectsInput');
    if (!input) return;
    const raw = input.value || "";
    subjects = raw.split(',').map(s => s.trim()).filter(Boolean);
}

function renderSubjects() {
    const list = document.getElementById('subjectList');
    if (!list) return;
    list.innerHTML = '';
    subjects.forEach((s, idx) => {
        const span = document.createElement('span');
        span.className = 'chip';
        span.innerText = s + ' ';
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.innerText = 'x';
        removeBtn.onclick = () => { removeSubject(idx); };
        span.appendChild(removeBtn);
        list.appendChild(span);
    });
    // update hidden/visible input
    const input = document.getElementById('subjectsInput');
    if (input) input.value = subjects.join(', ');
}

function addSubject() {
    const name = prompt("Enter Subject Name:");
    if (!name) return;
    subjects.push(name.trim());
    renderSubjects();
}

function removeSubject(index) {
    subjects.splice(index, 1);
    renderSubjects();
}

document.addEventListener('DOMContentLoaded', function () {
    // initialize from existing input value
    parseSubjectsInput();
    renderSubjects();
});

