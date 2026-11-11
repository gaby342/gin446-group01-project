/* =========================================================================
   GIN446 – Web Programming · Chapter 7 - JavaScript Part 2
   Lab 06: Review Before You Submit

   Student name : ______________________________
   Student ID   : ______________________________

   Only HTML, CSS and JavaScript. Do not modify profile.html, style.css or
   confirmation.html: all your work is in this file.
   Test often: save, reload profile.html (F5), keep the console open (F12).
   ========================================================================= */

// The elements you need (already selected for you)
const form = document.getElementById("profile-form");
const panel = document.getElementById("review");
const list = document.getElementById("review-list");
const editBtn = document.getElementById("edit-btn");
const confirmBtn = document.getElementById("confirm-btn");


/* TASK 1 + TASK 2 – Intercept and validate the submission
   - Listen to the "submit" event of the form.
   - Cancel its default action, so the page stays here.
   - If the form is not valid: show the browser's warnings and stop.
   - If it is valid: showReview(collectData());                               */
form.addEventListener("submit", function(event) {
  event.preventDefault();

  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  showReview(collectData());
});

/* TASK 3 – Collect every value
   Return an ARRAY of objects { label, value }, one per field, for example:
      [ { label: "Full name", value: "Lea Haddad" },
        { label: "Skills",    value: "programming, ai" }, ... ]
   Fields: fullname, email, studentId, age, major, graduation (radio),
           skills (checkboxes), software (multiple select), bio, consent.   */
function collectData() {
  const rows = [];

  const labels = {
    fullname: "Full name",
    email: "Email",
    studentId: "Student ID",
    age: "Age",
    major: "Major",
    graduation: "Expected graduation",
    skills: "Skills",
    software: "Software",
    bio: "Bio",
    consent: "Consent"
  };

  const fieldNames = [
    "fullname",
    "email",
    "studentId",
    "age",
    "major",
    "graduation",
    "skills",
    "software",
    "bio",
    "consent"
  ];

  fieldNames.forEach(function(name) {
    const field = form.elements[name];

    if (!field) return;

    let value;

    if (name === "skills") {
      const checked = [...form.querySelectorAll('input[name="skills"]:checked')].map(function(input) {
        return input.value;
      });
      value = checked.join(", ");
    } else if (name === "software") {
      const selected = [...field.selectedOptions].map(function(option) {
        return option.value;
      });
      value = selected.join(", ");
    } else if (field.type === "radio") {
      const checkedRadio = form.querySelector('input[name="' + name + '"]:checked');
      value = checkedRadio ? checkedRadio.value : "";
    } else if (field.type === "checkbox") {
      value = field.checked ? field.value : "";
    } else {
      value = field.value;
    }

    rows.push({ label: labels[name], value: value });
  });

  return rows;
}

/* TASK 4 – Fill and open the review panel
   For each row: create a <dt> (label) and a <dd> (value) with createElement,
   fill them with textContent, append them to the list.
   Clear the list first. Then hide the form and open the panel (classList). */

function showReview(rows) {
  list.textContent = "";

  rows.forEach(function(row) {
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");

    dt.textContent = row.label;
    dd.textContent = row.value;

    list.appendChild(dt);
    list.appendChild(dd);
  });

  form.classList.add("hidden");
  panel.classList.add("open");
}

/* TASK 5 – Edit: close the panel and show the form again (no reload).      */
editBtn.addEventListener("click", function() {
  panel.classList.remove("open");
  form.classList.remove("hidden");
});


/* TASK 6 – Confirm & Submit: send the form to confirmation.html,
   WITHOUT firing the "submit" event again (no loop).                       */

confirmBtn.addEventListener("click", function() {
  form.submit();
});