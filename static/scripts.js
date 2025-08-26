const argsDropdown = document.getElementById('argsCount');
const argsContainer = document.getElementById('argsContainer');
const doctestsDropdown = document.getElementById('doctestsCount');
const doctestsContainer = document.getElementById('doctestsContainer');
const functionNameInput = document.getElementById('function_name');
const returnTypeInput = document.getElementById('returnType');

document.addEventListener("DOMContentLoaded", function () {
    const dotContainer = document.querySelector(".dot-container");
    const numberOfDots = 50; // Number of dots

    for (let i = 0; i < numberOfDots; i++) {
        let dot = document.createElement("div");
        dot.classList.add("dot");

        // Random horizontal positioning (spread across the screen)
        dot.style.left = `${Math.random() * 100}vw`;

        // Start dots at random heights, but move them upwards
        dot.style.bottom = `${Math.random() * 100}vh`;

        // Random animation speed (5s to 15s)
        let duration = Math.random() * 10 + 7;
        dot.style.animationDuration = `${duration}s`;

        // Random delay for natural effect (0s to 5s)
        dot.style.animationDelay = `${Math.random() * 0.1}s`;

        // Append the dot to the container
        dotContainer.appendChild(dot);
    }
});

function updateDoctestDivs() {
    const functionName = functionNameInput.value.trim() || "function_name"; // Use the current function name or default if empty
    const doctestDivs = Array.from(doctestsContainer.querySelectorAll('.doctestBox'));
    doctestDivs.forEach((div, index) => {
        div.innerHTML = `
            <span>>>> ${functionName}</span>
            <input type="text" name="doctest_${index + 1}" class="styledInput doctestInput" placeholder="(type)"><br>
            <input type="text" name="output_${index + 1}" class="styledInput doctestOutput" placeholder="type"><br>
        `;
    });
    updateDoctestInputPlaceholder();
    updateDoctestOutputPlaceholder();
}

argsDropdown.addEventListener('change', () => {
    const count = parseInt(argsDropdown.value);
    document.getElementById('number_of_arguments').value = count;
    argsContainer.innerHTML = '';
    for (let i = 1; i <= count; i++) {
    const input = document.createElement('input');
    input.type = 'text';
    input.name = `argument_${i}`;
    input.placeholder = `arg${i}: type`;  // kept consistent with Python format
    input.classList.add("styledInput");
    input.addEventListener('input', updateDoctestInputPlaceholder);
    argsContainer.appendChild(input);
    argsContainer.appendChild(document.createElement('br'));
}

    updateDoctestInputPlaceholder();
});

doctestsDropdown.addEventListener('change', () => {
    const count = parseInt(doctestsDropdown.value);
    document.getElementById('number_of_doctests').value = count;
    doctestsContainer.innerHTML = '';
    for (let i = 1; i <= count; i++) {
        const doctestDiv = document.createElement('div');
        doctestDiv.className = 'doctestBox';
        doctestsContainer.appendChild(doctestDiv);
    }
    updateDoctestDivs(); // Ensure the function name persists
});

function updateDoctestInputPlaceholder() {
    const args = Array.from(argsContainer.querySelectorAll('input')).map(input => input.value).filter(Boolean);
    const inputPlaceholder = args.length > 0 ? `(${args.join(', ')})` : '(type)';
    const doctestInputs = doctestsContainer.querySelectorAll('input[name^="doctest_"]');
    doctestInputs.forEach(input => {
        input.placeholder = inputPlaceholder;
    });
}

function updateDoctestOutputPlaceholder() {
    const returnType = returnTypeInput.value.trim() || 'type';
    const doctestOutputs = doctestsContainer.querySelectorAll('input[name^="output_"]');
    doctestOutputs.forEach(output => {
        output.placeholder = returnType;
    });
}

functionNameInput.addEventListener('input', () => {
    updateDoctestDivs(); // Rebuild doctests with the updated function name
});

returnTypeInput.addEventListener('input', () => {
    updateDoctestOutputPlaceholder();
});

// Add functionality for Clear Selection button
function clearSelection() {
    document.getElementById('functionForm').reset();

    // Reset number of arguments to 0 and clear the argsContainer
    document.getElementById('number_of_arguments').value = 0;
    argsContainer.innerHTML = '';

    // Reset number of doctests to 1 and update the doctestsContainer
    document.getElementById('number_of_doctests').value = 1;
    doctestsDropdown.value = 1;
    doctestsContainer.innerHTML = '';
    const initialDoctestDiv = document.createElement('div');
    initialDoctestDiv.className = 'doctestBox';
    doctestsContainer.appendChild(initialDoctestDiv);

    // Rebuild doctests and placeholders with default values
    updateDoctestDivs();
    updateDoctestInputPlaceholder();
    updateDoctestOutputPlaceholder();
}

updateDoctestDivs(); // Initialize the doctests with default function name


