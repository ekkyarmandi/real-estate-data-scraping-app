async function debugThis(property_id, value) {
  const url = `/api/v1/debug?id=${property_id}&is_debug=${value}`;
  console.log(url);
  const response = await fetch(url);
  if (response.ok) {
    const debugButton = document.getElementById(property_id).querySelector(".btn-debug");
    // update debug state
    debugButton.setAttribute("onclick", `debugThis('${property_id}', ${!value})`);
    if (value) {
      // if debug is set to true, change color to red
      debugButton.classList.replace("bg-blue-500", "bg-red-500");
      debugButton.classList.replace("hover:bg-blue-600", "hover:bg-red-600");
    } else {
      // if debug is set to true, change color to blue
      debugButton.classList.replace("bg-red-500", "bg-blue-500");
      debugButton.classList.replace("hover:bg-red-600", "hover:bg-blue-600");
    }
  }
}

function substractNumberOfIssue(labelName) {
  const missingLabels = document.querySelectorAll("#missing-labels li p");
  const invalidLabels = document.querySelectorAll("#invalid-labels li p");
  // const excludedTags = document.querySelectorAll("#excuded-tags li p");
  const labels = [...missingLabels, ...invalidLabels];
  labels.forEach((label) => {
    var count = label.getAttribute("count");
    countInt = parseInt(count);
    const is_the_label = label.getAttribute("onclick").includes(labelName);
    if (is_the_label) {
      countInt = countInt - 1;
      const countSpan = label.querySelector("span:last-child");
      countSpan.innerHTML = `(${countInt.toLocaleString()})`;
      label.setAttribute("count", countInt);
    }
  });
}

async function deleteThis(element, property_id) {
  try {
    // put loading spinner
    element.innerHTML = `<span class="animate-pulse">Loading..</span>`;
    // making a fetch
    const response = await fetch("/api/v1/dashboard/property?id=" + property_id, { method: "DELETE" });
    const result = await response.json();
    if (response.ok) {
      const mainContainer = element.closest("div[id]");
      // get all labels
      const labels = mainContainer.querySelectorAll("div.labels p.label");
      // update missing labels value on the left
      labels.forEach((label) => {
        const name = label.textContent.trim();
        substractNumberOfIssue(name);
      });
      // remove the component
      element.innerHTML = "<span>DELETE</span>";
      mainContainer.remove();
    }
  } catch (err) {
    console.log(err);
  }
}

function changeText(element, newValue, cssSelector) {
  if (newValue == "CANCEL") {
    const prevWidth = element.offsetWidth;
    element.setAttribute("style", "width: " + prevWidth + "px");
  } else {
    element.removeAttribute("style");
  }
  element.querySelector(cssSelector).textContent = newValue;
}

async function cancelExclusion(element) {
  const property_id = element.closest("div[id]").getAttribute("id");
  const response = await fetch("/api/v1/dashboard/property/cancel-exclusion?id=" + property_id, { method: "PATCH" });
  const result = await response.json();
  console.log(result);
  if (response.ok) {
    element.remove()
  }
}

const exclusionBadge = (label) => {
  return `
    <p
      class="exclusion transform ease-in-out cursor-pointer rounded-full bg-orange-500 hover:bg-orange-600 font-mono text-xs w-fit px-2 py-1 text-center whitespace-nowrap"
      onmouseover="changeText(this, 'CANCEL', 'span')"
      onmouseout="changeText(this, '${label}', 'span')"
      onclick="cancelExclusion(this)">
      <span>${label}</span>
    </p>`;
}

async function exclusionHandler(element) {
  const mainContainer = element.closest("div[id]");
  const propertyId = mainContainer.getAttribute("id");
  // check existings exclusion labels
  const res = await fetch(`/api/v1/dashboard/source/exclusion?id=${propertyId}&new_value=${element.value}`, { method: "PATCH" });
  if (res.ok) {
    const data = await res.json();
    const excludedLabel = mainContainer.querySelector(".exclusion");
    if (excludedLabel) {
      // update the exclusion label
      excludedLabel.querySelector("span").textContent = element.value;
      excludedLabel.setAttribute("onmouseout", `changeText(this,'${element.value}', 'span')`);
    } else {
      // append new exclusion label
      const labelsContainer = mainContainer.querySelector(".labels");
      const newLabel = exclusionBadge(element.value);
      labelsContainer.insertAdjacentHTML("beforeend", newLabel);
    }
  }
}

function labelsListener() {
  const labels = document.querySelectorAll(".labels .label");
  labels.forEach((labelElement) => {
    labelElement.addEventListener("contextmenu", async (event) => {
      event.preventDefault();
      const element = event.target.tagName == "SPAN" ? event.target.parentElement : event.target;
      verifiedLabel(element);
    });
  });
}

async function verifiedLabel(element) {
  const label = element.querySelector("span").textContent;
  const id = element.closest("div[id]").getAttribute("id");
  return await fetch(`/api/v1/dashboard/label/${label}/verify?id=${id}`)
    .then((res) => {
      if (res.ok) {
        // substract from the sidebar
        substractNumberOfIssue(label);
        // remove element from listing
        element.remove();
      }
    })
    .catch((err) => console.log(err));
}

const propertyCard = (prop) => {
  const labelBadge = (label) => {
    return `
      <p
        class="label cursor-pointer rounded-full bg-emerald-500 hover:bg-emerald-600 font-mono text-xs w-fit px-2 py-1 text-center whitespace-nowrap">
        <span onclick="getProperties('${label}')">${label}</span>
      </p>`;
  };
  prop.labels = prop.labels.map((label) => labelBadge(label));
  if (prop.excluded_by) {
    const exclusionLabel = exclusionBadge(prop.excluded_by);
    prop.labels.push(exclusionLabel);
  }
  return `
      <div id="${prop.id}" class="flex justify-between gap-2 items-start rounded-md p-2 bg-slate-700 hover:bg-slate-600 h-auto">
        <div class="flex flex-col justify-between h-full">
          <div>
            <p class="font-bold text-[#B6ED34]">
            <span>${prop.source}</span>
            ${!prop.is_available ? `<span class="uppercase text-red-500">[${prop.availability_text}]</span>` : ""}
            <span class="text-white font-medium">1 of ${prop.history.length + 1}</span>
            </p>
            <h3 class="mb-1">
              <a class="hover:underline hover:text-blue-500" href="${prop.url}" target="_blank">${prop.title}</a>
            </h3>
            <div class="flex flex-wrap gap-1 text-xs">
              <p class="border rounded-md px-2 py-1 hover:bg-slate-700 hover:cursor-default whitespace-nowrap">
                <span>Contract:</span>
                <span id="contract-type">${prop.contract_type}</span>
                <span id="leasehold-years" value=${prop.leasehold_years}>${prop.leasehold_years ? `(${prop.leasehold_years.toLocaleString()} yr)` : ""}</span>
              </p>
              <p class="border rounded-md px-2 py-1 hover:bg-slate-700 hover:cursor-default whitespace-nowrap">
                <span>Type:</span>
                <span id="property-type">${prop.property_type}</span>
              </p>
              <p class="border rounded-md px-2 py-1 hover:bg-slate-700 hover:cursor-default whitespace-nowrap">
                <span>Price:</span>
                <span id="currency" value="${prop.currency.toLowerCase()}">${prop.currency == "USD" ? "$" : "Rp"}</span>
                <span id="price" value="${prop.price}">${prop.price ? prop.price.toLocaleString() : null}</span>
              </p>
              <p class="border rounded-md px-2 py-1 hover:bg-slate-700 hover:cursor-default whitespace-nowrap">
                <span>Bedrooms:</span>
                <span id="bedrooms" value="${prop.bedrooms}">${prop.bedrooms ? prop.bedrooms : null}</span>
              </p>
              <p class="border rounded-md px-2 py-1 hover:bg-slate-700 hover:cursor-default whitespace-nowrap">
                <span>Bathrooms:</span>
                <span id="bathrooms" value="${prop.bathrooms}">${prop.bathrooms ? prop.bathrooms : null}</span>
              </p>
              <p class="border rounded-md px-2 py-1 hover:bg-slate-700 hover:cursor-default whitespace-nowrap">
                <span>Build Size:</span>
                <span id="build-size" value="${prop.build_size}">${prop.build_size ? prop.build_size.toLocaleString() : null}</span>
              </p>
              <p class="border rounded-md px-2 py-1 hover:bg-slate-700 hover:cursor-default whitespace-nowrap">
                <span>Land Size:</span>
                <span id="land-size" value="${prop.land_size}">${prop.land_size ? prop.land_size.toLocaleString() : null}</span>
              </p>
              <p class="border rounded-md px-2 py-1 hover:bg-slate-700 hover:cursor-default whitespace-nowrap">
                <span>Location:</span>
                <span id="location"">${prop.location ? prop.location : null}</span>
              </p>
            </div>
            <div class="labels flex flex-wrap gap-1 mt-2">${prop.labels.join("\n")}</div>
          </div>
          <div class="flex gap-1 mt-2 items-center">
            <button class="text-sm px-2 py-1 rounded-sm bg-blue-500 hover:bg-blue-600" onclick="editThis(this)">EDIT</button>
            <button class="btn-debug text-sm px-2 py-1 rounded-sm ${prop.is_debug == "true" ? "bg-red-500 hover:bg-red-600" : "bg-blue-500 hover:bg-blue-600"}" onclick="debugThis('${prop.id}', ${prop.is_debug == "true" ? "false" : "true"})">DEBUG</button>
            <button class="text-sm px-2 py-1 rounded-sm bg-blue-500 hover:bg-blue-600" onclick="deleteThis(this,'${prop.id}')">DELETE</button>
            <select class="exclude-menu text-sm rounded-sm bg-blue-500 hover:bg-blue-600 px-2 py-1 w-28" onchange="exclusionHandler(this)">
              <option>EXCLUDE</option>
              ${prop.exclusions}
            </select>
            <p class="text-sm font-mono">${prop.scraped_at}</p>
          </div>
        </div>
        <img class="aspect-[4/3] rounded-md bg-cover" src="${prop.image_url}" style="min-height: 115px; max-height: 175px; width: auto"/>
      </div>
    `;
};

class Property {
  constructor(propertyElement, formElement) {
    this.container = propertyElement.closest("div[id]");
    this.id = this.container.getAttribute("id");
    this.popup = formElement;
    this.card = {
      title: this.container.querySelector("h3 a"),
      type: this.container.querySelector("#property-type"),
      contract: this.container.querySelector("#contract-type"),
      years: this.container.querySelector("#leasehold-years"),
      currency: this.container.querySelector("#currency"),
      price: this.container.querySelector("#price"),
      bedrooms: this.container.querySelector("#bedrooms"),
      bathrooms: this.container.querySelector("#bathrooms"),
      build_size: this.container.querySelector("#build-size"),
      land_size: this.container.querySelector("#land-size"),
      location: this.container.querySelector("#location"),
    }
    this.form = {
      id: this.popup.querySelector("h3"),
      title: this.popup.querySelector("table tr:has(label[for=title]) td input"),
      type: this.popup.querySelector("table tr:has(label[for=property-type]) td input"),
      contract: this.popup.querySelector("table tr:has(label[for=contract-type]) td input"),
      years: this.popup.querySelector("table tr:has(label[for=leasehold-years]) td input"),
      currency: this.popup.querySelector("select#currency"),
      price: this.popup.querySelector("table tr:has(label[for=price]) td input"),
      bedrooms: this.popup.querySelector("table tr:has(label[for=bedrooms]) td input"),
      bathrooms: this.popup.querySelector("table tr:has(label[for=bathrooms]) td input"),
      build_size: this.popup.querySelector("table tr:has(label[for=build-size]) td input"),
      land_size: this.popup.querySelector("table tr:has(label[for=land-size]) td input"),
      location: this.popup.querySelector("table tr:has(label[for=location]) td input"),
    }
  }
  show() {
    this.popup.classList.replace("hidden", "fixed");
  }
  close() {
    this.popup.classList.replace("fixed", "hidden");
  }
  getFormValue() {
    const data = {
      id: this.id,
      title: this.form.title.value,
      type: this.form.type.value,
      contract: this.form.contract.value,
      years: this.form.years.value,
      currency: this.form.currency.value,
      price: this.form.price.value,
      bedrooms: this.form.bedrooms.value,
      bathrooms: this.form.bathrooms.value,
      build_size: this.form.build_size.value,
      land_size: this.form.land_size.value,
      location: this.form.location.value,
    };
    return this.validate(data);
  }
  getPropertyValue() {
    const data = {
      id: this.id,
      title: this.card.title.textContent,
      type: this.card.type.textContent,
      contract: this.card.contract.textContent,
      years: this.card.years?.getAttribute("value"),
      currency: this.card.currency?.getAttribute("value"),
      price: this.card.price?.getAttribute("value"),
      bedrooms: this.card.bedrooms?.getAttribute("value"),
      bathrooms: this.card.bathrooms?.getAttribute("value"),
      build_size: this.card.build_size?.getAttribute("value"),
      land_size: this.card.land_size?.getAttribute("value"),
      location: this.card.location.textContent,
    };
    return this.validate(data);
  }
  validate(dict) {
    const integerGroup = ["price", "build_size", "land_size"];
    const floatGroup = ["years", "bedrooms", "bathrooms"];
    for (const key in dict) {
      const value = dict[key];
      // parse null
      if (value == "null" || value.trim() == "") {
        dict[key] = null;
      } else if (floatGroup.includes(key)) {
        // parse float
        try {
          dict[key] = parseFloat(value);
        } catch (err) {
          dict[key] = null;
        }
      } else if (integerGroup.includes(key)) {
        // parse integer
        try {
          dict[key] = parseInt(value);
        } catch (err) {
          dict[key] = null;
        }
      } else if (key == "currency") {
        dict[key] = value.toUpperCase();
      }
    }
    return dict;
  }
  populateForm() {
    const data = this.getPropertyValue();
    this.form.id.textContent = `Edit Property ID: ${this.id}`;
    this.form.title.value = data.title;
    this.form.type.value = data.type;
    this.form.contract.value = data.contract;
    this.form.years.value = data.years;
    this.form.currency.value = data.currency.toLowerCase();
    this.form.price.value = data.price;
    this.form.bedrooms.value = data.bedrooms;
    this.form.bathrooms.value = data.bathrooms;
    this.form.build_size.value = data.build_size;
    this.form.land_size.value = data.land_size;
    this.form.location.value = data.location;
  }
  syncProperty() {
    const newData = this.getFormValue();
    this.card.title.textContent = newData.title;
    this.card.type.textContent = newData.type;
    this.card.contract.textContent = newData.contract;
    this.card.years.textContent = newData.years ? `(${newData.years.toLocaleString()} yr)` : "";
    this.card.years.setAttribute("value", newData.years);
    this.card.currency.textContent = newData.currency == "USD" ? "$" : "Rp";
    this.card.currency.setAttribute("value", newData.currency);
    this.card.price.textContent = newData.price?.toLocaleString();
    this.card.price.setAttribute("value", newData.price);
    this.card.bedrooms.textContent = newData.bedrooms?.toLocaleString();
    this.card.bedrooms.setAttribute("value", newData.bedrooms);
    this.card.bathrooms.textContent = newData.bathrooms?.toLocaleString();
    this.card.bathrooms.setAttribute("value", newData.bathrooms);
    this.card.build_size.textContent = newData.build_size?.toLocaleString();
    this.card.build_size.setAttribute("value", newData.build_size);
    this.card.land_size.textContent = newData.land_size?.toLocaleString();
    this.card.land_size.setAttribute("value", newData.land_size);
    this.card.location.textContent = newData.location;
  }
  loading() {
    const updateBtn = this.popup.querySelector(".update-btn");
    updateBtn.classList.add("animate-pulse");
    updateBtn.textContent = "Loading..";
  }
  idle() {
    const updateBtn = this.popup.querySelector(".update-btn");
    updateBtn.classList.remove("animate-pulse");
    updateBtn.textContent = "Update";
  }
  async update() {
    // change state update to loading..
    this.loading();
    // fetch property
    const eventHandler = () => {
      // change state update to idle
      this.idle();
      // sync property
      this.syncProperty();
      // close popup
      this.close();
    };
    // setTimeout(eventHandler, 2000);
    const newData = this.getFormValue();
    await fetch("/api/v1/dashboard/property", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(newData),
    }).then(eventHandler).catch((err) => console.log(err));
  }
}

async function editThis(element) {
  const popup = document.querySelector("form.popup");
  var property = new Property(element, popup);
  // show popup
  property.show();
  // populate the form input columns
  property.populateForm();
  // create handler functions
  const cancelHandler = () => {
    property?.close();
    property = null;
    updateBtn.removeEventListener("click", updateHandler);
  }
  const updateHandler = () => {
    property.update();
    property = null;
    updateBtn.removeEventListener("click", updateHandler);
  }
  // add event listener to update button
  const updateBtn = popup.querySelector(".update-btn");
  updateBtn.addEventListener("click", updateHandler);
  // add event listener to cancel button
  const cancelBtn = popup.querySelector(".cancel-btn");
  cancelBtn.addEventListener("click", cancelHandler);
}

// [x] Fix property update issue
// [ ] Add refresh button for a single property
// [x] Add verified button on the label
// [ ] Figure out how to prevent the editied / modified data to be change back on the extraction
// [ ] Add functionality to bulk edit the property type
// [ ] Add functionality to bulk exclude the property type
// [ ] Add functionality to bulk delete the excluded or unwanted property type