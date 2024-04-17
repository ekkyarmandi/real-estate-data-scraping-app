// [ ] construct next/previous page url for next and prev button

function definePagination() {
  // get the url path
  const pagination = document.getElementById("pagination");
  const prevPageBtn = pagination.querySelector("button.prev-btn");
  const nextPageBtn = pagination.querySelector("button.next-btn");
  // get max page
  var max_page = pagination.querySelector("p span:last-child").textContent;
  // get the page number
  var page;
  const queryString = new URLSearchParams(window.location.search)
  if (queryString.has("page")) {
    page = queryString.get("page");
  } else {
    page = 1;
  }
  // reconstruct the page number
  if (page == 1) {
    // disable prev page
    prevPageBtn.setAttribute("disabled", true);
    prevPageBtn.querySelector("a").setAttribute("href", "#");
    // create next url
    const nextUrl = window.location.pathname + "?page=" + (parseInt(page) + 1);
    nextPageBtn.querySelector("a").setAttribute("href", nextUrl);
  } else if (page < max_page) {
    console.log(page, max_page);
    // -1 for prev page
    const prevUrl = window.location.pathname + "?page=" + (parseInt(page) - 1);
    prevPageBtn.querySelector("a").setAttribute("href", prevUrl);
    prevPageBtn.removeAttribute("disabled");
    // +1 for next page
    const nextUrl = window.location.pathname + "?page=" + (parseInt(page) + 1);
    nextPageBtn.querySelector("a").setAttribute("href", nextUrl);
    nextPageBtn.removeAttribute("disabled");
  } else if (page == max_page) {
    // disable next page
    const prevUrl = window.location.pathname + "?page=" + (parseInt(page) - 1);
    prevPageBtn.querySelector("a").setAttribute("href", prevUrl);
    nextPageBtn.setAttribute("disabled", true);
    nextPageBtn.querySelector("a").setAttribute("href", "#");
  }
}

// init
definePagination();