function toggleOutputField(index, action, defaultValue) {
    const reasonField = document.getElementById(`rejectReason_${index}`);
    const outputField = document.getElementById(`output_${index}`);

    if (action === "reject") {
        reasonField.style.display = "inline-block";
        outputField.value = ""; // reset
        reasonField.addEventListener("input", function () {
            outputField.value = reasonField.value;
        });
    } else {
        reasonField.style.display = "none";
        outputField.value = defaultValue;
    }
}
