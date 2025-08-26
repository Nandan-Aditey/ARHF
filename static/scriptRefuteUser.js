document.addEventListener('DOMContentLoaded', function () {
    const dropdown = document.getElementById('doctestsCount');
    const container = document.getElementById('doctestsContainer');
    const functionName = container.getAttribute('data-function-name');  // Retrieve the function name

    dropdown.addEventListener('change', function () {
        const count = parseInt(dropdown.value);
        container.innerHTML = ""; // Clear old inputs

        for (let i = 1; i <= count; i++) {
            const box = document.createElement('div');
            box.className = 'doctestBox';
            box.innerHTML = `
                <span class="doctestFunction">>>> ${functionName}</span><br>
                <input type="text" name="doctest_${i}" class="styledInput doctestInput" placeholder="(type)"><br>
                <input type="text" name="output_${i}" class="styledInput doctestOutput" placeholder="type"><br>
            `;
            container.appendChild(box);
        }
    });

    dropdown.dispatchEvent(new Event('change'));  // Trigger once on load
});
