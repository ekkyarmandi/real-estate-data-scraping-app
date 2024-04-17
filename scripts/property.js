function replaceWord(text, targetWord, replacementWord) {
  const regex = new RegExp(targetWord, 'gi');
  return text.replace(regex, replacementWord);
}

function findWords() {
  const keyword = document.querySelector("h1 span:last-child").textContent;
  const paragraphs = document.querySelectorAll("li div > p");
  paragraphs.forEach(p => {
    const span = `<span class="bg-yellow-500 text-black">${keyword}</span>`
    p.innerHTML = replaceWord(p.textContent, keyword.toLowerCase(), span);
  })
  const titles = document.querySelectorAll("li h3 > a");
  titles.forEach(t => {
    const span = `<span class="bg-yellow-500 text-black">${keyword}</span>`
    t.innerHTML = replaceWord(t.textContent, keyword.toLowerCase(), span);
  })
}

findWords();