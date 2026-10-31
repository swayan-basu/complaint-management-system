function setStatusMessage(message, isError = false) {
    const result = document.getElementById("status_result");
    result.textContent = message;
    result.style.color = isError ? "#c62828" : "";
}

async function copyTrackingId() {
    const input = document.getElementById("track_input_id");
    const button = document.getElementById("copytrackBtn");
    const trackingId = input.value.trim();

    if (!trackingId) {
        setStatusMessage("Please enter a valid tracking ID.", true);
        return;
    }

    try {
        await navigator.clipboard.writeText(trackingId);
        button.textContent = "Tracking ID Copied!";
        setTimeout(() => {
            button.textContent = "Copy ID";
        }, 2000);
    } catch (error) {
        console.error("Failed to copy tracking ID:", error);
        setStatusMessage("Copy failed. Please copy the tracking ID manually.", true);
    }
}

async function checkStatus() {
    const input = document.getElementById("track_input_id");
    const trackingId = input.value.trim();

    if (!trackingId) {
        setStatusMessage("Please enter a valid tracking ID.", true);
        return;
    }

    setStatusMessage("Checking status...");
    try {
        const response = await fetch(`/api/track/${encodeURIComponent(trackingId)}`);
        const data = await response.json();
        if (!response.ok || !data.success) {
            setStatusMessage(data.error || "Unable to find that complaint.", true);
            return;
        }
        setStatusMessage(`Status: ${data.status.toUpperCase()}`);
    } catch (error) {
        console.error("Failed to fetch complaint status:", error);
        setStatusMessage("Connection failed. Please try again.", true);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("copytrackBtn").addEventListener("click", copyTrackingId);
    document.getElementById("checkStatusBtn").addEventListener("click", checkStatus);

    const resetBtn = document.querySelector("button.resetbtn") || document.querySelector(".reset-btn");
    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            document.getElementById("track_input_id").value = "";
            document.getElementById("status_result").textContent = ""; 

            if (window.history.replaceState) {
                window.history.replaceState({}, document.title, window.location.pathname);
            }
        });
    }
    const input = document.getElementById("track_input_id");
    if (input.value && navigator.clipboard) {
        navigator.clipboard.writeText(input.value).catch((error) => {
            console.info("Automatic tracking ID copy was not permitted:", error);
        });
    }
});
