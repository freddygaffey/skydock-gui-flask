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

const POLL_INTERVAL = 1000;

// Function to poll the backend for new questions
async function pollForQuestion() {
    while (true) {
        try {
            const res = await fetch("/incoming_question");
            const question = await res.text();

            if (question && question !== "None") {
                // Ask the user
                const accept = confirm(`Drone asks: "${question}"\nDo you accept?`);

                // Send response back to the backend
                await fetch("/question_answer", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ command: accept ? "Accepted" : "Rejected", question: question })
                });

                document.getElementById("status").innerText = `Last question: "${question}" - ${accept ? "Accepted" : "Rejected"}`;
            }
        } catch (error) {
            console.error("Error polling for question:", error);
        }

        // Wait before polling again
        await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));
    }
}

// Start polling when the page loads
document.addEventListener("DOMContentLoaded", pollForQuestion);
