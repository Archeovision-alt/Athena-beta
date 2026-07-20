/* ==================================================

   ATHENA Beta 0.2
   Script interaction utilisateur

================================================== */


const button = document.getElementById(
    "ask-button"
);


const questionBox = document.getElementById(
    "question"
);


const thinking = document.getElementById(
    "thinking"
);


const answerBox = document.getElementById(
    "answer"
);



button.addEventListener(
    "click",
    async function()

{


    const question = questionBox.value.trim();



    if(question === "") {

        return;

    }



    // Nettoyage ancienne réponse

    answerBox.innerHTML = "";

    answerBox.classList.add(
        "hidden"
    );



    // Affichage Thinking

    thinking.classList.remove(
        "hidden"
    );



    button.disabled = true;



    try {


        const response = await fetch(
            "/ask",
            {

                method: "POST",

                headers: {

                    "Content-Type":
                    "application/json"

                },


                body: JSON.stringify({

                    question: question

                })

            }
        );



        const data = await response.json();



        answerBox.innerHTML =
            data.answer.replace(
                /\n/g,
                "<br>"
            );



        answerBox.classList.remove(
            "hidden"
        );



    }


    catch(error) {


        answerBox.innerHTML =

        "Une erreur est survenue lors de la communication avec ATHENA.";


        answerBox.classList.remove(
            "hidden"
        );


        console.error(error);


    }



    finally {


        thinking.classList.add(
            "hidden"
        );


        button.disabled = false;


    }



});