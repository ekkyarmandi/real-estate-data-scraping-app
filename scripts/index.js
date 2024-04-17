// Download URLs
async function downloadURLs() {
  // Update button state
  const btn = document.getElementById("check-missing-urls");
  btn.classList.add("animate-spin");
  // Make a GET requests
  const response = await fetch("/api/spreadsheet-urls")
    .then((res) => res.json())
    .catch((err) => {
      console.log(err);
      if (btn.classList.contains("animate-spin")) {
        btn.classList.remove("animate-spin");
      }
    });
  // Update the number of urls
  const missingURLs = document.getElementById("missing-urls");
  missingURLs.textContent = response.count.toLocaleString();
  // Update missing-urls tag
  updateMissingUrlsHref(response.urls);
  // Update button back
  btn.classList.remove("animate-spin");
}

function updateMissingUrlsHref(urls) {
  const aTag = document.getElementById("missing-urls");
  // add the href value
  aTag.setAttribute("href", "/spreadsheet-urls/?urls=" + urls.join(","));
  // add the underline class
  if (!aTag.classList.contains("underline")) {
    aTag.classList.add("underline");
    aTag.classList.add("text-blue-500");
  }
}

// Dropdown menu actions
const allCaretBtn = document.querySelectorAll("button.actions");
allCaretBtn.forEach((btn) => {
  const menu = btn.parentElement.querySelector("#action-menu");
  btn.addEventListener("click", () => {
    menu.classList.remove("hidden");
  })
})

function action(element, cmd, value, types) {
  const container = element.parentElement;
  container.classList.add("hidden");
  switch (cmd) {
    case 'rename':
      console.log('rename', value);
      const p = document.getElementById(value);
      const input = paragraphToInput(p);
      const prevValue = input.value;
      input.addEventListener("keydown", (event) => {
        if (event.key === 'Enter') {
          // get input value
          if (input.value != prevValue) {
            // update the properties value with new one
            fetch("/api/update", {
              method: "POST",
              headers: {
                "Accept": "application/json",
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                column: types,
                previous_value: prevValue,
                new_value: input.value,
              })
            })
            window.location = "/"
          }
          // convert back into paragraph
          inputToParagrah(input, types);
        }
      })
      break;
    case 'show-exclude-menu':
      // get the relative container
      const divRelative = element.closest("div.relative");
      // add back the hidden to the first ul
      const actionMenu = divRelative.querySelector("#action-menu");
      actionMenu.classList.add("hidden");
      // // remove the hidden from the latest ul
      const excludeMenu = divRelative.querySelector("#exclude-menu");
      excludeMenu.classList.remove("hidden");
      break;
    case 'exclude':
      async function excludeAll(property_type, exclude_criterion) {
        const response = await fetch(`/api/bulk-exclude?property_type=${property_type}&by=${exclude_criterion}`);
        if (response.status == 200) {
          const divRelative = element.closest("div.relative");
          divRelative.parentElement.remove(divRelative);
        }
      }
      excludeAll(value, types);
      break;
  }
}

function paragraphToInput(paragraph) {
  const inputElement = document.createElement("input");
  inputElement.setAttribute("type", "text");
  inputElement.setAttribute("data-count", paragraph.getAttribute("data-count"));
  inputElement.value = paragraph.getAttribute("data-name");
  inputElement.classList.add("ps-2", "py-1", "bg-transparent", "border", "border-indigo-500", "rounded-md");
  paragraph.parentElement.replaceChild(inputElement, paragraph);
  inputElement.focus();
  return inputElement;
}

function inputToParagrah(inputElement, types) {
  const newValue = inputElement.value;
  const count = inputElement.getAttribute("data-count");
  const paragraph = document.createElement("a");
  const kind = types == "contract-type" ? "ct-" : "pt-"
  paragraph.setAttribute("id", kind + newValue);
  paragraph.setAttribute("data-name", newValue);
  paragraph.setAttribute("data-count", count);
  paragraph.setAttribute("href", `/${types}/?value=${newValue}`);
  paragraph.setAttribute("target", "_blank");
  paragraph.classList.add("py-1", "hover:underline")
  const nameSpan = document.createElement("span");
  nameSpan.textContent = newValue + " ";
  const countSpan = document.createElement("span");
  countSpan.textContent = `(${count})`
  paragraph.insertAdjacentElement("beforeEnd", nameSpan);
  paragraph.insertAdjacentElement("beforeEnd", countSpan);
  inputElement.parentElement.replaceChild(paragraph, inputElement);
}

document.addEventListener("click", (element) => {
  // console.log(element.target);
  if (element.target.tagName != "svg" && element.target.tagName != "path") {
    const allActionMenus = document.querySelectorAll("#action-menu");
    allActionMenus.forEach((e) => {
      if (!e.classList.contains("hidden")) {
        e.classList.add("hidden");
      }
    })
    // document.querySelectorAll("#exclude-menu").forEach((e) => {
    //   if (!e.classList.contains("hidden")) {
    //     e.classList.add("hidden");
    //   }
    // })
  }
})

async function setTab(element) {
  element.classList.add("animate-pulse");
  element.classList.replace("bg-indigo-500", "bg-sky-500");
  const response = await fetch("/api/define-tab");
  if (response.status == 200) {
    element.classList.remove("animate-pulse");
    element.classList.replace("bg-sky-500", "bg-indigo-500");
  }
}

// define the selected period or default value
function setPeriod(period) {
  localStorage.setItem("selectedPeriod", period);
  document.getElementById("period").setAttribute("value", period);
}
const period = document.getElementById("period");
// update selected value based on previous selected
const prevPeriod = localStorage.getItem("selectedPeriod");
if (prevPeriod) {
  period.value = prevPeriod;
  console.log(prevPeriod);
}
period.querySelectorAll("option").forEach((element) => {
  if (element.value == period.value) {
    element.setAttribute("selected", true);
    setPeriod(period.value);
  } else {
    element.removeAttribute("selected");
  }
})
period.addEventListener("change", (element) => {
  setPeriod(element.target.value);
})