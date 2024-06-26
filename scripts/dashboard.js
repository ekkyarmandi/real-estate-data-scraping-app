async function getInfo(date) {
  const setContainer = (data, isLoading) => {
    const info = document.getElementById("info");
    info.innerHTML = ""; // reset info container 
    const container = document.createElement("ul");
    const liTotalScraped = document.createElement("li");
    const liTotalNewScraped = document.createElement("li");
    const loadingText = `<span class="animate-pulse">Loading..</span>`;
    liTotalScraped.innerHTML = "Total Scraped: "
    liTotalNewScraped.innerHTML = "Total New Scraped: "
    container.insertAdjacentElement("beforeend", liTotalScraped);
    container.insertAdjacentElement("beforeend", liTotalNewScraped);
    if (isLoading) {
      liTotalScraped.insertAdjacentHTML("beforeend", loadingText);
      liTotalNewScraped.insertAdjacentHTML("beforeend", loadingText);
    } else {
      liTotalScraped.innerHTML = `
        <span>Total Scraped:</span>
        <span>${data.total_scraped.toLocaleString()}</span>
        <span>(${data.extracted_percentage.toFixed(2)}% extracted)</span>
      `;
      liTotalNewScraped.innerHTML = `
        <span>Total New Scraped:</span>
        <span>${data.total_new_scraped.toLocaleString()}</span>
        <span>(${data.new_extracted_percentage.toFixed(2)}% extracted, ${data.new_excluded_percentage.toFixed(2)}% excluded)</span>
      `;
    }
    info.insertAdjacentElement("beforeend", container);
  }
  // constract request parameters
  const params = new URLSearchParams({ date: date });
  // set the status to loading state
  var isLoading = true;
  setContainer({}, isLoading);
  // making a GET request
  await fetch("/api/v1/dashboard/total?" + params.toString())
    .then(async (res) => {
      // update the info container
      const data = await res.json();
      var isLoading = false;
      setContainer(data, isLoading);
    })
    .catch((err) => console.log(err));
}

async function getNewInfo(date) {
  const params = new URLSearchParams({ date: date })
  const response = await fetch("/api/v1/dashboard/new-info?" + params.toString());
  const data = await response.json();
  const info = document.getElementById("new-info");
  info.innerHTML = "";
  const content = `
  <ul>
    <li>
      <p>
        <span>Has Missing Values:</span>
        <span>${data.total_missing_values.toLocaleString()}</span>
        <span>(<span class="text-gray-400">${data.total_missing_solved.toFixed(2)}%</span>)</span>
      </p>
    </li>
    <li>
      <p>
        <span>Has Invalid Values:</span>
        <span>${data.total_invalid_values.toLocaleString()}</span>
        <span>(<span class="text-gray-400">${data.total_invalid_solved.toFixed(2)}%</span>)</span>
      </p>
    </li>
  </ul>`;
  info.insertAdjacentHTML("BeforeEnd", content);
}

function showSpreadsheetResult() {
  const newLiTag = (item) => {
    return `<li>
      <p><a class="text-blue-500 underline" href="${item.url}" target="_blank">${item.url}</a></p>
      <p class="mt-1 mb-2 text-black px-[4px] bg-yellow-500 w-fit">${item.exclusion}</p>
    </li>`
  };
  // get the urls
  const content = document.querySelector("body script").textContent;
  const results = JSON.parse(content);
  // put on results column
  const container = document.getElementById("results");
  container.innerHTML = "";
  const ulTag = document.createElement("ul");
  ulTag.classList.add("list-disc", "ps-1");
  results.forEach((item) => {
    ulTag.insertAdjacentHTML("beforeend", newLiTag(item));
  });
  container.insertAdjacentElement("beforeend", ulTag);
}

async function getSpreadsheetURLs() {
  const data = await fetch("/api/v1/dashboard/sheet").then(res => res.json()).catch((err) => console.log(err));
  // put the total value under information
  const info = document.getElementById("sheet-info");
  // change word loading to downloading
  info.querySelectorAll("span.animate-pulse").forEach((tag) => {
    tag.textContent = "Downloading now.."
  })
  info.innerHTML = "";
  info.insertAdjacentHTML("beforeend", `
    <ul>
      <li><p><span>Unscraped URLs: </span><span>${data.count.toLocaleString()}</span></p></li>
      <li><p><span>Not Yet Excluded: </span><span>${data.count_excluded.toLocaleString()}</span></p></li>
    </ul>
    <button class="px-2 py-1 bg-blue-500 mt-2 rounded-md" type="button" onclick="showSpreadsheetResult()">Show</button>`
  );
  // store data below script
  const script = document.createElement("script");
  script.setAttribute("type", "application/json");
  script.textContent = JSON.stringify(data.results);
  document.querySelector("body script").insertAdjacentElement("beforebegin", script);
}

function createPagination(label, page, max_page) {
  // clear the previous pagination
  const prev = document.querySelector(".pagination");
  prev && prev.remove();
  // create new pagination
  const container = document.getElementById("results");
  const pagination = document.createElement("div");
  pagination.classList.add("pagination", "flex", "gap-1", "mb-2", "ps-2");
  for (let i = 1; i <= max_page; i++) {
    const colorStyle = i == page ? "text-black bg-[#B6ED34]" : "bg-blue-500";
    const isActive = i == page ? "active" : "";
    const pageSpan = `<button class="aspect-square w-[28px] h-[28px] text-center text-sm rounded-sm p-1 ${colorStyle}" ${isActive} type="button" onclick="getProperties('${label}', ${i})">${i}</button>`;
    pagination.insertAdjacentHTML("BeforeEnd", pageSpan);
  }
  container.insertAdjacentElement("BeforeBegin", pagination);
}

async function getProperties(name, page = 1, is_exclusion = false) {
  // fetching the data
  const container = document.getElementById("results");
  const data = await fetch("/api/v1/dashboard/label/" + name + "?page=" + page + "&is_exclusion=" + is_exclusion).then(res => res.json()).catch((e) => { console.log(e) });
  // put data on the container
  container.innerHTML = "";
  data.results.forEach((item) => {
    item.exclusions = Array.from(document.querySelectorAll("select#exclusions option")).map(
      (e) => {
        const cloned = e.cloneNode(true);
        return cloned.outerHTML;
      });
    container.insertAdjacentHTML("beforeend", propertyCard(item))
  });
  // create labels event listener
  labelsListener();
  // create pagination
  createPagination(name, data.page, data.max_page);
  // put the title before pagination
  const pagination = document.querySelector(".pagination");
  const title = pagination.parentElement.querySelector("h2")
  if (!title) {
    const title = `<h2 class="font-bold text-lg ps-2">${name}</h2>`
    pagination.insertAdjacentHTML("beforebegin", title);
  } else {
    title.textContent = name;
  }
}

async function getPropertiesOnType(date, propertyType, page = 1) {
  // fetching the data
  const params = new URLSearchParams({ date: date, type: propertyType, page: page })
  const container = document.getElementById("results");
  const data = await fetch("/api/v1/dashboard/property-types/unit?" + params.toString()).then(res => res.json()).catch((err) => { console.log(err) });
  // put data on the container
  container.innerHTML = "";
  data.results.forEach((item) => {
    item.exclusions = Array.from(document.querySelectorAll("select#exclusions option")).map(
      (e) => {
        const cloned = e.cloneNode(true);
        return cloned.outerHTML;
      });
    container.insertAdjacentHTML("beforeend", propertyCard(item))
  });
  // create labels event listener
  labelsListener();
}

async function getPropertyLabels(date) {
  const params = new URLSearchParams({ date: date })
  const data = await fetch("/api/v1/dashboard/labels?" + params.toString()).then(res => res.json()).catch((err) => console.log(err));
  const labelLink = (label) => {
    return `<li>
      <p class="hover:cursor-pointer hover:text-blue-500 hover:underline font-mono text-sm w-fit" count=${label.count} onclick=getProperties('${label.label}')>
        <span>${label.name}</span>
        <span>(${label.count.toLocaleString()})</span>
      </p>
    </li>`
  };
  const labelConstructor = (container, labels) => {
    container.innerHTML = "";
    if (labels?.length > 0) {
      labels.forEach((item) => {
        container.insertAdjacentHTML("BeforeEnd", labelLink(item));
      });
    } else {
      container.innerHTML = "<p class='font-mono text-sm text-green-500'>Clear</p>";
    }
  };
  const missingContainer = document.getElementById("missing-labels");
  labelConstructor(missingContainer, data.missing);
  const invalidContainer = document.getElementById("invalid-labels");
  labelConstructor(invalidContainer, data.invalid);
}

async function getPropertyExcludedBy(date) {
  const params = new URLSearchParams({ date: date });
  const data = await fetch("/api/v1/dashboard/exclusions?" + params.toString()).then(res => res.json()).catch((err) => console.log(err));
  const labelLink = (label) => {
    return `<li>
      <p class="hover:cursor-pointer hover:text-blue-500 hover:underline font-mono text-sm w-fit" count=${label.count} onclick=getProperties('${label.name}',1,true)>
        <span>#${label.name}</span>
        <span>(${label.count.toLocaleString()})</span>
      </p>
    </li>`
  };
  const labelConstructor = (container, labels) => {
    container.innerHTML = "";
    if (labels?.length > 0) {
      labels.forEach((item) => {
        container.insertAdjacentHTML("BeforeEnd", labelLink(item));
      });
    } else {
      container.innerHTML = "<p class='text-sm font-mono'>Clear</p>";
    }
  };
  const missingContainer = document.getElementById("excluded-tags");
  labelConstructor(missingContainer, data);
}

function showDropDownOnPropertyType(element) {
  // show the element
  element.querySelector("ul").classList.replace("hidden", "inline");
}

function hideMenu(element) {
  element.querySelector("ul").classList.replace("inline", "hidden");
}

function editMode(element) {
  // get the element container
  const container = element.closest("li.container");
  const text = container.querySelector("p span").textContent;
  // store the count in a hidden element
  const count = container.querySelector("p span[count]").getAttribute("count");
  const countContainer = `<input class="hidden" count=${count} value="${text}" />`;
  // convert p into input on edit
  const input = document.createElement("input");
  input.classList.add("px-2", "py-1", "border", "text-sm", "rounded-md", "bg-transparent");
  input.setAttribute("value", text);
  container.querySelector("p").outerHTML = input.outerHTML;
  // append the count into container
  container.insertAdjacentHTML("afterbegin", countContainer);
  // hide menu
  hideMenu(container);
  // add enter event listener: enter to save
  // const editHandler = (event) => {
  //   console.log(event);
  //   // remove event listener
  //   container.removeEventListener(input, editHandler);
  // }
  input.addEventListener("keydown", (event) => { console.log(event); });
}

// <div class="relative rounded-full hover:bg-slate-600" style="width: 20px; height: 20px; padding: 4px" onclick="showDropDownOnPropertyType(this)">
//   <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512" fill="white"><path d="M8 256a56 56 0 1 1 112 0A56 56 0 1 1 8 256zm160 0a56 56 0 1 1 112 0 56 56 0 1 1 -112 0zm216-56a56 56 0 1 1 0 112 56 56 0 1 1 0-112z"/></svg>
//   <ul class="hidden absolute top-0 left-0 z-10">
//     <li class="cursor-pointer px-2 py-1 text-sm bg-slate-700 hover:bg-slate-600 rounded-t-md" onclick="editMode(this)">Edit</li>
//     <li class="cursor-pointer px-2 py-1 text-sm bg-slate-700 hover:bg-slate-600 rounded-b-md" onclick="excludeMode(this)">Exclude</li>
//   </ul>
// </div>

async function getUniquePropertyType(date) {
  const propertyType = (param) => {
    return `
      <li class="container flex gap-2 items-center">
        <p class="text-sm font-mono hover:underline hover:text-blue-500 cursor-pointer" onclick="getPropertiesOnType('${param.date}','${param.type.name}')">
          <span>${param.type.name}</span>
          <span count=${param.type.count}>(${param.type.count.toLocaleString()})</span>
        </p>
      </li>`;
  }
  const container = document.getElementById("property-types");
  const params = new URLSearchParams({ date: date })
  const response = await fetch("/api/v1/dashboard/property-types?" + params.toString());
  if (response.ok) {
    const results = await response.json();
    container.innerHTML = "";
    if (results.length > 0) {
      results.forEach((text) => {
        // append property type li into container
        container.insertAdjacentHTML("beforeend", propertyType({ type: text, date: date }));
      });
    } else {
      container.innerHTML = '<span class="font-mono text-sm">Villa (0)</span>';
    }
  }
}

async function loadWorkbook() {
  // get the date
  const selectedDate = document.getElementById("period").value;
  // get the workbook
  const selectedWorkbook = document.getElementById("workbook").value;
  console.log(selectedDate, selectedWorkbook);
  // make a get requests
  await fetch(`/api/dev?date=${selectedDate}&workbook=${selectedWorkbook}`)
    .then((res) => {
      // show the main container
      document.querySelector(".main-container").classList.remove("hidden");
      // load the data
      getInfo(selectedDate);
      getNewInfo(selectedDate);
      // getSpreadsheetURLs();
      getPropertyLabels(selectedDate);
      getPropertyExcludedBy(selectedDate);
      getUniquePropertyType(selectedDate);
    })
    .catch((err) => console.log(err));
  // show the result on the screen
}

function assignEventHandler() {
  const loadBtn = document.querySelector(".btn-load");
  loadBtn.addEventListener("click", loadWorkbook);
}

// init
assignEventHandler();
// getProperties('missing_bathrooms');