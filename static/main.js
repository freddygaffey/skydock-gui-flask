document.addEventListener("DOMContentLoaded", function() {

    // General function to set up a button with optional parameter
    function setupButton(buttonId, command, parameterId) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.addEventListener("click", function() {
                let payload = { command: command };
                if (parameterId) {
                    const parameter = document.getElementById(parameterId).value;
                    payload.parameter = parameter;
                }
                fetch("/command", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.status);
                })
                .catch(error => console.error("Error:", error));
            });
        }
    }

    // Make buttons here
    setupButton("takeoffBtn", "takeoff", "takeoffHeight");

});
