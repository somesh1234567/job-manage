const employeeRadio = document.getElementById("employeeRadio");
const phoneField = document.getElementById("phoneField");
const resumeField = document.getElementById("resumeField");

employeeRadio.addEventListener("change", function () {
    if (employeeRadio.checked) {
        phoneField.classList.add("hidden");
        resumeField.classList.add("hidden");
    } else {
        phoneField.classList.remove("hidden");
        resumeField.classList.remove("hidden");
    }
});