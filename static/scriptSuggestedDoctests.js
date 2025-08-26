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

function toggleOutputField(index, action, expectedValue) {
    const rejectReasonInput = document.getElementById(`rejectReason_${index}`);
    const outputField = document.getElementById(`output_${index}`);

    if (action === 'reject') {
        rejectReasonInput.style.display = "block";
        outputField.value = rejectReasonInput.value;  // User entered value
    } else {
        rejectReasonInput.style.display = "none";
        outputField.value = expectedValue;  // Use the numeric value (e.g., 0)
    }
}
