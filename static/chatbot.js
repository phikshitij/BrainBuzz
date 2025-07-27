document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const chatBox = document.getElementById("chat-box");
    const clearBtn = document.getElementById("clear-chat-btn");

    form.addEventListener("submit", async function(e) {
        e.preventDefault();
        const message = input.value.trim();
        if (!message) return;
        // Show user message instantly
        chatBox.innerHTML += `<div class='mb-3'><div><strong>You:</strong> ${message}</div></div>`;
        input.value = "";
        // Send to backend
        const resp = await fetch("/teacher/chatbot/ajax", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message})
        });
        const data = await resp.json();
        chatBox.innerHTML += `<div class='mb-3'><div class='text-success'><strong>AI:</strong> ${data.response}</div><div class='text-muted' style='font-size:0.8em;'>${data.timestamp}</div><hr/></div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    });

    if (clearBtn) {
        clearBtn.addEventListener("click", async function() {
            await fetch("/teacher/chatbot/clear", {method: "POST"});
            chatBox.innerHTML = "<div class='text-muted'>No chat history yet. Ask your first question below!</div>";
        });
    }
});
