const groupmates = [
    {name: 'Денис', surname: 'Уваров', group: 'БСТ2351', marks: [4, 3, 5]},
    {name: 'Иван', surname: 'Петров', group: 'БСТ0001', marks: [4, 4, 4]},
    {name: 'Кирилл', surname: 'Смирнов', group: 'БСТ0001', marks: [5, 5, 5]},
    {name: 'Анна', surname: 'Соколова', group: 'БСТ0001', marks: [5, 4, 5]},
    {name: 'Мария', surname: 'Кузнецова', group: 'БСТ0001', marks: [3, 3, 4]},
    {name: 'Дмитрий', surname: 'Волков', group: 'БСТ0001', marks: [4, 5, 4]},
    {name: 'Елена', surname: 'Орлова', group: 'БСТ0002', marks: [4, 4, 4]},
    {name: 'Сергей', surname: 'Белов', group: 'БСТ0002', marks: [3, 4, 4]}
];

function averageMark(student) {
    return student.marks.reduce((sum, mark) => sum + mark, 0)
        / student.marks.length;
}

function filterByGroup(students, group) {
    return students.filter(student =>
        student.group.toUpperCase() === group.trim().toUpperCase());
}

function filterByAverage(students, threshold) {
    return students.filter(student => averageMark(student) > threshold);
}

function printStudents(students) {
    const pad = (value, width) => String(value).padEnd(width);
    console.log(pad('Имя', 15), pad('Фамилия', 15), pad('Группа', 12), 'Оценки');
    for (const student of students) {
        console.log(pad(student.name, 15), pad(student.surname, 15),
                    pad(student.group, 12), student.marks.join(', '));
    }
}

function showStudents(students) {
    const body = document.getElementById('students-body');
    body.replaceChildren();
    for (const student of students) {
        const row = document.createElement('tr');
        const values = [student.name, student.surname, student.group,
                        student.marks.join(', '), averageMark(student).toFixed(2)];
        for (const value of values) {
            const cell = document.createElement('td');
            cell.textContent = value;
            row.appendChild(cell);
        }
        body.appendChild(row);
    }
    document.getElementById('student-status').textContent = `Найдено студентов: ${students.length}`;
    printStudents(students);
}

document.getElementById('group-form').addEventListener('submit', event => {
    event.preventDefault();
    const group = document.getElementById('group-input').value.trim();
    if (!group) {
        document.getElementById('student-status').textContent = 'Введите группу';
        return;
    }
    document.getElementById('average-input').value = '';
    showStudents(filterByGroup(groupmates, group));
});

document.getElementById('average-form').addEventListener('submit', event => {
    event.preventDefault();
    const value = document.getElementById('average-input').value.trim();
    if (value === '' || !Number.isFinite(Number(value))) {
        document.getElementById('student-status').textContent = 'Введите средний балл';
        return;
    }
    document.getElementById('group-input').value = '';
    showStudents(filterByAverage(groupmates, Number(value))); 
});

document.getElementById('show-all').addEventListener('click', () => {
    document.getElementById('group-input').value = '';
    document.getElementById('average-input').value = '';
    showStudents(groupmates);
});
console.log(groupmates);
showStudents(groupmates);
