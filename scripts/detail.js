// replace None value with Nan with style
function decoretNullValue() {
  const span = document.querySelectorAll("span");
  span.forEach((element) => {
    if (element.innerText == "None" || element.innerText == "NaN") {
      element.classList.add("rounded", "font-mono", "text-xs", "text-violet-500", "bg-gray-300");
      element.setAttribute("style", "padding: 2px 4px")
      element.innerHTML = "NaN";
    }
  })
}

function removeCommas(value) {
  return value.replace(/(\d+),/g, "$1");
}

function toInputElement(element, tagName) {
  const p = element.closest("p");
  const lastSpan = p.querySelector("span:last-child");
  // create input
  const inputElement = document.createElement("input");
  // assign the value into the element
  if (tagName == "bedrooms" || tagName == "bathrooms" || tagName == "land_size" || tagName == "build_size" || tagName == "price") {
    inputElement.value = removeCommas(lastSpan.textContent);
  } else {
    inputElement.value = lastSpan.textContent;
  }
  inputElement.setAttribute("type", "text");
  inputElement.classList.add(tagName);
  inputElement.classList.add("bg-transparent", "rounded-md", "border", "border-violet-500");
  // replace the span tag with input tag
  p.replaceChild(inputElement, lastSpan);
  // event handler
  inputElement.addEventListener("keydown", saveOnEnter);
  return inputElement;
}

function toSelectCurrency(parent, span, name) {
  // create input
  const selectElement = document.createElement("select");
  const option1 = document.createElement("option");
  option1.innerText = "Rp";
  option1.setAttribute("value", "IDR");
  const option2 = document.createElement("option");
  option2.innerText = "$";
  option2.setAttribute("value", "USD");
  if (span.textContent == "Rp") {
    selectElement.value = "IDR";
    option1.setAttribute("selected", null);
  } else {
    selectElement.value = "USD";
    option2.setAttribute("selected", null);
  }
  selectElement.insertAdjacentElement("beforeend", option1);
  selectElement.insertAdjacentElement("beforeend", option2);
  selectElement.classList.add(name);
  selectElement.classList.add("bg-transparent", "rounded-md", "border", "border-violet-500");
  // replace the span tag with input tag
  parent.replaceChild(selectElement, span);
}


// Edit property
function editProperty(element) {
  const li = element.closest("li");
  // convert the type column into input
  const spans = li.querySelectorAll("span");
  spans.forEach(span => {
    const text = span.textContent;
    if (text.includes("type")) {
      const inputElement = toInputElement(span, "property-type");
      inputElement.focus();
    } else if (text.includes("location")) {
      toInputElement(span, "location");
    } else if (text.includes("tab")) {
      toInputElement(span, "tab");
    } else if (text.includes("Bedrooms")) {
      toInputElement(span, "bedrooms");
    } else if (text.includes("Bathrooms")) {
      toInputElement(span, "bathrooms");
    } else if (text.includes("Land Size")) {
      toInputElement(span, "land_size");
    } else if (text.includes("Build Size")) {
      toInputElement(span, "build_size");
    } else if (text.includes("price")) {
      toInputElement(span, "price");
      // to select
      const p = span.closest("p");
      const secondSpan = p.querySelector("span:nth-child(2)");
      toSelectCurrency(p, secondSpan, "price");
    }
  });
  // convert the edit button into save button
  element.innerText = "Save";
  element.setAttribute("onclick", "saveProperty(this)");
}

async function saveOnEnter(element) {
  if (element.key === "Enter") {
    const li = element.target.closest("li");
    const button = li.querySelector("button.edit-btn");
    await saveProperty(button);
  }
}

async function saveProperty(element) {
  const validateValue = (value) => {
    return isNaN(value) ? 0 : parseFloat(value);
  }
  const li = element.closest("li");
  // get value
  const propertyTypeInput = li.querySelector("input.property-type");
  const locationInput = li.querySelector("input.location");
  const priceInput = li.querySelector("input.price");
  const bedroomsInput = li.querySelector("input.bedrooms");
  const bathroomsInput = li.querySelector("input.bathrooms");
  const landSizeInput = li.querySelector("input.land_size");
  const buildSizeInput = li.querySelector("input.build_size");
  const tabInput = li.querySelector("input.tab");
  const currencySelect = li.querySelector("select.price");
  const inputElements = [
    propertyTypeInput,
    locationInput,
    priceInput,
    bedroomsInput,
    bathroomsInput,
    landSizeInput,
    buildSizeInput,
    tabInput,
  ];
  // update the data in the database using endpoint
  const payload = {
    url: li.querySelector("a").getAttribute("href"),
    property_type: propertyTypeInput.value,
    location: locationInput.value,
    currency: currencySelect.value,
    price: validateValue(priceInput.value),
    bedrooms: validateValue(bedroomsInput.value),
    bathrooms: validateValue(bathroomsInput.value),
    land_size: validateValue(landSizeInput.value),
    build_size: validateValue(buildSizeInput.value),
    tab: tabInput.value,
  }
  await fetch("/api/edit", {
    method: "POST",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  // convert back input element into span
  inputElements.forEach((inputElement) => {
    const p = inputElement.closest("p");
    const span = document.createElement("span");
    const value = inputElement.value;
    const classes = inputElement.classList;
    if (!isNaN(value) && (classes.contains("price") || classes.contains("land_size") || classes.contains("build_size"))) {
      span.innerText = parseInt(inputElement.value).toLocaleString();
    } else {
      span.innerText = inputElement.value;
    }
    p.replaceChild(span, inputElement);
  })
  // convert back the select element into a span tag
  const spanForSelect = document.createElement("span");
  if (currencySelect.value == "USD") {
    spanForSelect.innerText = "$";
  } else if (currencySelect.value == "IDR") {
    spanForSelect.innerText = "Rp";
  }
  currencySelect.parentElement.replaceChild(spanForSelect, currencySelect);
  // convert the save button back into edit button
  element.innerText = "Edit";
  element.setAttribute("onclick", "editProperty(this)");
  //
  decoretNullValue();
}


// find all verified button
const verificationButtons = document.querySelectorAll("button.verification-btn");
verificationButtons.forEach((element) => {
  // listen to click
  element.addEventListener("click", async (event) => {
    const li = event.target.closest("li");
    const url = li.querySelector("a").getAttribute("href");
    // get the button label
    const container = event.target.closest("div");
    const label = container.querySelector("a").textContent;
    const labels = [];
    container.parentElement.querySelectorAll("a").forEach((e) => { labels.push(e.textContent) });
    // make a fetch request and flag the is_verified to 1
    const endpoint = `/api/verified?url=${url}&label=${label}`;
    const response = await fetch(endpoint);
    // remove the property from the list when there's no other labels in the listing
    if (response.status == 200) {
      if (labels.length == 1 || window.location.pathname.includes(label)) {
        li.parentElement.removeChild(li);
      } else {
        container.parentElement.removeChild(container);
      }
    }
  })
})

var toRedButton = (btn) => {
  btn.classList.replace("bg-blue-600", "bg-red-600");
  btn.classList.replace("hover:bg-blue-700", "hover:bg-red-700");
  btn.setAttribute("onclick", "debugThis(this, false)");
  btn.innerText = "Cancel"
}

var toBlueButton = (btn) => {
  btn.classList.replace("bg-red-600", "bg-blue-600");
  btn.classList.replace("hover:bg-red-700", "hover:bg-blue-700");
  btn.setAttribute("onclick", "debugThis(this, true)");
  btn.innerText = "Debug"
}

// set the property to debug
async function debugThis(element, status) {
  const li = element.closest("li");
  const url = li.querySelector("a").getAttribute("href");
  const response = await fetch(`/api/debug?url=${url}&status=${status}`);
  if (response.status == 200) {
    if (status) {
      li.classList.replace("bg-slate-800", "bg-blue-800");
      toRedButton(element);
    } else {
      li.classList.replace("bg-blue-800", "bg-slate-800");
      toBlueButton(element);
    }
  }
}

async function checkIsDebug() {
  // collect all links
  const links = [];
  const aTags = document.querySelectorAll("li a");
  aTags.forEach((e) => { links.push(e.getAttribute("href")) });
  const response = await fetch("/api/is-debug?url=" + links.join(","));
  if (response.status == 200) {
    const data = await response.json()
    aTags.forEach((e) => {
      const li = e.closest("li");
      const btn = li.querySelector("button.debug-btn");
      const url = e.getAttribute("href");
      if (data.urls.includes(url)) {
        li.classList.replace("bg-slate-800", "bg-blue-800");
        toRedButton(btn);
      }
    });
  }
}

async function excludeThis(element) {
  const li = element.closest("li");
  const url = li.querySelector("a").getAttribute("href");
  const response = await fetch(`/api/exclude?url=${url}&by=${element.value}`);
  if (response.status == 200) {
    li.parentElement.removeChild(li);
  }
}

// init
decoretNullValue();
checkIsDebug();
