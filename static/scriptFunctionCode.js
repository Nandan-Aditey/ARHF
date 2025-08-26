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

function copyCode() {
    const codeBlock = document.getElementById('codeBlock');
    const range = document.createRange();
    range.selectNodeContents(codeBlock);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);

    try {
        document.execCommand('copy');
        alert('Code copied to clipboard!');
    } catch (err) {
        alert('Failed to copy code. Please try manually.');
    }

    selection.removeAllRanges();
}

// Wait for DOM to be fully loaded before adding event listeners
document.addEventListener("DOMContentLoaded", function () {
    const doneButton = document.getElementById("doneButton");

    if (doneButton) {
        doneButton.addEventListener("click", function () {
            fetch("/delete-file", { method: "POST" })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.href = "/completion"; // Redirect after deletion
                    } else {
                        alert("Error deleting the file: " + (data.error || "Unknown error"));
                    }
                })
                .catch(error => console.error("Error:", error));
        });
    }
});
