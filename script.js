/* ==================================================
   ATHENA Beta 0.2 - Script interaction utilisateur
================================================== */

// Test GitHub Desktop

/*
==================================================
HISTORIQUE DE LA CONVERSATION
==================================================
*/

let conversationHistory = [];

const button = document.getElementById("ask-button");
const questionBox = document.getElementById("question");
const thinking = document.getElementById("thinking");
const answerBox = document.getElementById("answer");

if (button) {
    button.addEventListener("click", async function () {

        if (!questionBox) return;

        const question = questionBox.value.trim();

        if (question === "") {
            return;
        }

        /*
        ==============================================
        AJOUT DE LA QUESTION À L'HISTORIQUE
        ==============================================
        */

        conversationHistory.push({
            role: "user",
            content: question
        });

        /*
        ==============================================
        CONSTRUCTION DU CONTEXTE
        ==============================================
        */

        let contextualQuestion = "";

        conversationHistory.forEach(function (message) {
            if (message.role === "user") {
                contextualQuestion += "\n\nUSER:\n" + message.content;
            }

            if (message.role === "assistant") {
                contextualQuestion += "\n\nATHENA:\n" + message.content;
            }
        });

        // Nettoyage ancienne réponse
        if (answerBox) {
            answerBox.innerHTML = "";
            answerBox.classList.add("hidden");
        }

        // Affichage Thinking
        if (thinking) {
            thinking.classList.remove("hidden");
        }

        button.disabled = true;

        try {
            const response = await fetch("/ask", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question: contextualQuestion
                })
            });

            const data = await response.json();

            /*
            ==============================================
            AJOUT DE LA RÉPONSE À L'HISTORIQUE
            ==============================================
            */

            const answerText = data.answer || "Pas de réponse.";

            conversationHistory.push({
                role: "assistant",
                content: answerText
            });

            if (answerBox) {
                answerBox.innerHTML = answerText.replace(/\n/g, "<br>");
                answerBox.classList.remove("hidden");
            }

        } catch (error) {
            if (answerBox) {
                answerBox.innerHTML = "Une erreur est survenue lors de la communication avec ATHENA.";
                answerBox.classList.remove("hidden");
            }
            console.error(error);
        } finally {
            if (thinking) {
                thinking.classList.add("hidden");
            }
            button.disabled = false;
        }

    }); // La fermeture est maintenant correcte ici !
}