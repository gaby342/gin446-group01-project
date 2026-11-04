/* =========================================================================
   GIN446 – Web Programming · Chapter 6 - JavaScript Part 1
   Lab05 (60 min): build a 5-question quiz with JavaScript

   Student name : ______________________________
   Student ID   : ______________________________

   Rules: 
   Work in PART 1. Do not modify PART 2 (provided helpers).
   Test often: save, reload the page (F5) and read the console (F12).
   ========================================================================= */


/* =========================================================================
   PART 1 – YOUR CODE
   ========================================================================= */

/* TASK 1 – The questions (10 min)
   Each question is an object with 3 properties:
     question : the text of the question            (string)
     choices  : the 4 possible answers               (array of strings)
     answer   : the INDEX of the correct choice      (number: 0, 1, 2 or 3)
   The first question is given. Add 4 questions (5 in total) about the
   basics of Chapter 6. At least one question must have answer: 0.        */
const questions = [
  {
    question: "Which keyword declares a variable that cannot be reassigned?",
    choices: ["var", "let", "const", "static"],
    answer: 2,
  },
  {
    question: "Which method is used to join all elements of an array into a string?",
    choices: ["join()","concat()", "toString()", "split()"],
    answer: 0,
  },
  {
    question: "What is the output of typeof null in JavaScript?",
    choices: ["null", "object", "undefined", "boolean"],
    answer: 1,
  },
  {
    question: "Which symbol is used for strict equality comparison?",
    choices: ["==", "===", "!=", "!=="],
    answer: 1,
  },
  {
    question: "Which loop is guaranteed to run at least once?",
    choices: ["for loop", "while loop", "do...while loop", "foreach loop"],
    answer: 2,
  },
  {
  question: "Which operator is used to assign a value to a variable?",
  choices: ["=", "==", "===", ":"],
  answer: 0,
},
];

function buildQuestionHTML(q, index) {
  let html = "";
html+=`<div class=question>
<p class=question-text>${index+1}. ${q.question}</p>`
for(let i=0;i<q.choices.length;i++){
  html+=`<label class = choice><input type = "radio" name = "q${index}" value = "${i}">${q.choices[i]}</label>`
}
html+=`</div>`
return html;
}

function renderQuiz() {
  let html = "";
 for(let i=0;i<questions.length;i++){
  html+=buildQuestionHTML(questions[i],i)
 }showInPage("quiz",html);
}

function calculateScore() {
  let score = 0;
for(let i=0;i<questions.length;i++){
  const selected = getSelectedAnswer(i);
  if(selected === questions[i].answer){
    score++;
  }
}
score= score * 100 / questions.length;
  return Math.round(score);
}

function getMessage(score) {
  if (score === 100) {
    return "Excellent! You master the basics.";
  } else if (score > 60 && score < 100) {
    return "Good job, review the questions you missed.";
  } else {
    return "Review Chapter 6 and try again.";
  }
}

function submitQuiz() {

 let html = "";
 html+=`<p class = "score">Score: ${Math.round(calculateScore() * questions.length / 100)}/${questions.length} (${calculateScore().toFixed(2)}%)</p>`
 html+=`<p class = "message"> ${getMessage(calculateScore())}</p>`
 for(let i = 0; i < questions.length ; i++){
  const selected = getSelectedAnswer(i);
  if(selected === undefined){
    html+=`<p class = "line unanswered">${i + 1}. Not answered – correct answer: ${questions[i].choices[questions[i].answer]}</p>`
  }else if(selected === questions[i].answer){
    html+=`<p class = "line correct">${i + 1}. Correct – ${questions[i].choices[selected]}</p>`
  }else{
    html+=`<p class = "line wrong">${i + 1}. Incorrect – your answer: ${questions[i].choices[selected]} · correct answer: ${questions[i].choices[questions[i].answer]}</p>`
  }
 }
 showInPage("result",html)
}


/* =========================================================================
   PART 2 – PROVIDED HELPERS (DOM, studied in Chapter 7) – DO NOT MODIFY
   ========================================================================= */

// Writes an HTML string inside the element that has this id.
function showInPage(id, html) {
  const element = document.getElementById(id);
  if (html === undefined || html === "") {
    element.innerHTML = `<p class="hint">Nothing to display in #${id} yet. ` +
      `Check that your function builds the HTML string and passes it to showInPage().</p>`;
    console.info(`showInPage("${id}") received an empty string.`);
    return;
  }
  element.innerHTML = html;
}

// Returns the index of the radio button checked for question i, or undefined.
function getSelectedAnswer(i) {
  const checked = document.querySelector(`input[name="q${i}"]:checked`);
  if (checked === null) {
    return undefined;
  }
  return Number(checked.value);
}

// Starts the quiz when the page is loaded.
renderQuiz();
if (document.getElementById("quiz").innerHTML === "") {
  showInPage("quiz", "");
}
